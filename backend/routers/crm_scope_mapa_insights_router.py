from __future__ import annotations

import re
import unicodedata
from collections import Counter
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers import strategic_layers_router as estrategia
from routers.crm_scope_estrategia_router import FECHADOS
from routers.crm_scope_mapa_equipe_router import (
    _crm_carteira,
    _deduplicar,
    _historico_base,
    _historico_carteira,
    _pode_gerir,
    _resolver_alvo,
    _usuario_regional,
)
from services.commercial_client_scope import filtrar_anfir_por_responsavel_comercial
from services.crm_live_projection import carregar_oportunidades_enriquecidas
from services.mapa_line_market import composicao_marca_linha
from services.mapa_perdas_direcionamento import direcionar_perda_dominante, direcionar_registros
from services.product_line_classifier import classificar_linha

router = APIRouter(prefix="/crm-seguro/mapa-equipe", tags=["crm-seguro-mapa-insights"])

MESES = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
MESES_CHAVES = {
    "JAN": 1, "JANEIRO": 1,
    "FEV": 2, "FEVEREIRO": 2,
    "MAR": 3, "MARCO": 3,
    "ABR": 4, "ABRIL": 4,
    "MAI": 5, "MAIO": 5,
    "JUN": 6, "JUNHO": 6,
    "JUL": 7, "JULHO": 7,
    "AGO": 8, "AGOSTO": 8,
    "SET": 9, "SETEMBRO": 9,
    "OUT": 10, "OUTUBRO": 10,
    "NOV": 11, "NOVEMBRO": 11,
    "DEZ": 12, "DEZEMBRO": 12,
}

STATUS_PERDA_ANFIR_2026 = {
    "NACIONAL",
    "TK",
    "USADOCONCORRENTE",
    "SEMCONTATO",
    "PERDIDO",
}


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def _valor(item: dict[str, Any]) -> float:
    try:
        return float(item.get("valor_estimado") or 0)
    except (TypeError, ValueError):
        return 0.0


def _quantidade(item: dict[str, Any], padrao: int = 1) -> int:
    try:
        valor = item.get("quantidade")
        if valor in (None, ""):
            return padrao
        return max(0, int(float(valor)))
    except (TypeError, ValueError):
        return padrao


def _linha_nome(item: dict[str, Any]) -> str:
    codigo = classificar_linha(item)
    return {"TR": "Trailer", "DT": "Diesel Truck", "DD": "Direct Drive"}.get(codigo, "Não classificado")


def _cliente_nome(item: dict[str, Any]) -> str:
    return str(
        item.get("cliente")
        or item.get("cliente_nome")
        or item.get("empresa")
        or item.get("transportadora")
        or item.get("razao_social")
        or ""
    ).strip()


def _carrier_confirmado(item: dict[str, Any]) -> bool:
    status = _fold(item.get("status")).replace(" ", "")
    fabricante = _fold(item.get("fabricante_equipamento"))
    return status in {"CARRIER", "USADOCARRIER"} or fabricante == "CARRIER"


def _ano_registro(item: dict[str, Any]) -> int | None:
    valor = item.get("ano")
    try:
        if valor not in (None, ""):
            ano = int(float(valor))
            if 2000 <= ano <= 2100:
                return ano
    except (TypeError, ValueError):
        pass

    for campo in ("data", "data_evento", "data_negociacao", "data_abertura", "created_at", "updated_at"):
        bruto = str(item.get(campo) or "").strip()
        if not bruto:
            continue
        match = re.search(r"\b(20\d{2})\b", bruto)
        if match:
            return int(match.group(1))
    return None


def _mes_registro(item: dict[str, Any]) -> int | None:
    bruto_mes = item.get("mes")
    if bruto_mes not in (None, ""):
        try:
            mes = int(float(bruto_mes))
            if 1 <= mes <= 12:
                return mes
        except (TypeError, ValueError):
            chave = _fold(bruto_mes)
            if chave in MESES_CHAVES:
                return MESES_CHAVES[chave]

    for campo in ("data", "data_evento", "data_negociacao", "data_abertura", "created_at", "updated_at"):
        bruto = str(item.get(campo) or "").strip()
        if not bruto:
            continue
        try:
            normalizado = bruto.replace("Z", "+00:00")
            return datetime.fromisoformat(normalizado).month
        except ValueError:
            pass
        match = re.search(r"(?:^|\D)(0?[1-9]|1[0-2])[/\-](?:20)?\d{2,4}(?:\D|$)", bruto)
        if match:
            return int(match.group(1))
        match = re.search(r"(?:^|\D)\d{1,2}[/\-](0?[1-9]|1[0-2])[/\-](?:20)?\d{2,4}(?:\D|$)", bruto)
        if match:
            return int(match.group(1))
    return None


def _data_evidencia(item: dict[str, Any]) -> str | None:
    for campo in ("data", "data_evento", "data_negociacao", "data_abertura", "updated_at", "created_at"):
        valor = str(item.get(campo) or "").strip()
        if valor:
            return valor[:10]
    mes = _mes_registro(item)
    ano = _ano_registro(item)
    if mes and ano:
        return f"{ano:04d}-{mes:02d}"
    return None


def _ultima_evidencia(registros: list[dict[str, Any]]) -> str | None:
    datas = [data for item in registros if (data := _data_evidencia(item))]
    return max(datas) if datas else None


def _serie_12() -> list[int]:
    return [0 for _ in range(12)]


def _somar_mes(serie: list[int], item: dict[str, Any], valor: int = 1) -> bool:
    mes = _mes_registro(item)
    if not mes:
        return False
    serie[mes - 1] += max(0, valor)
    return True


def _mercado_anfir_2026() -> list[dict[str, Any]]:
    mercado_total, _, _ = estrategia._anfir(
        "viena-sp",
        "PERSONALIZADO",
        None,
        None,
        date(2026, 1, 1),
        date(2026, 12, 31),
    )
    return [item for item in mercado_total if _ano_registro(item) in (None, 2026)]


def _anfir_do_escopo(alvo: UsuarioAutenticado | None, equipe: list[dict[str, Any]], mercado_total: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if alvo is not None:
        return filtrar_anfir_por_responsavel_comercial(list(mercado_total), str(alvo.id), alvo.nome)

    todos: list[dict[str, Any]] = []
    for registro in equipe:
        responsavel = _usuario_regional(registro)
        todos.extend(filtrar_anfir_por_responsavel_comercial(list(mercado_total), str(responsavel.id), responsavel.nome))
    return _deduplicar(todos)


def _fontes_do_escopo(
    alvo: UsuarioAutenticado | None,
    equipe: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    historico_base = _historico_base(date(2026, 1, 1), date(2026, 12, 31))
    crm_base = carregar_oportunidades_enriquecidas()
    if alvo is not None:
        return _historico_carteira(alvo, historico_base), _crm_carteira(alvo, crm_base)

    historico: list[dict[str, Any]] = []
    crm: list[dict[str, Any]] = []
    for registro in equipe:
        responsavel = _usuario_regional(registro)
        historico.extend(_historico_carteira(responsavel, historico_base))
        crm.extend(_crm_carteira(responsavel, crm_base))
    return _deduplicar(historico), _deduplicar(crm)


def _enriquecer_direcionamento(
    direcionamento: dict[str, Any],
    anfir: list[dict[str, Any]],
    historico: list[dict[str, Any]] | None = None,
    crm: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    historico = historico or []
    crm = crm or []
    for alvo in direcionamento.get("alvos") or []:
        chave = _fold(alvo.get("cliente"))
        if not chave:
            continue
        anf_cliente = [item for item in anfir if _fold(_cliente_nome(item)) == chave]
        hist_cliente = [item for item in historico if _fold(_cliente_nome(item)) == chave]
        crm_cliente = [item for item in crm if _fold(_cliente_nome(item)) == chave]
        crm_ativos = [item for item in crm_cliente if str(item.get("status") or "").upper() not in FECHADOS]
        concorrentes = Counter()
        for item in anf_cliente:
            status = str(item.get("status") or item.get("fabricante_equipamento") or "").strip()
            if status and not _carrier_confirmado(item):
                concorrentes[status] += _quantidade(item, 1)
        concorrente = concorrentes.most_common(1)[0][0] if concorrentes else None
        if crm_ativos:
            cobertura = "CRM_ATIVO"
        elif crm_cliente:
            cobertura = "CRM_SEM_ATIVO"
        else:
            cobertura = "SEM_CRM"
        alvo["fontes"] = {
            "anfir": {
                "ocorrencias": len(anf_cliente),
                "unidades": sum(_quantidade(item, 1) for item in anf_cliente),
            },
            "historico": {
                "registros": len(hist_cliente),
                "unidades": sum(_quantidade(item, 0) for item in hist_cliente),
            },
            "crm": {
                "registros": len(crm_cliente),
                "ativos": len(crm_ativos),
                "pipeline": round(sum(_valor(item) for item in crm_ativos), 2),
            },
        }
        alvo["cobertura"] = cobertura
        alvo["concorrencia"] = concorrente
        alvo["temporalidade"] = {
            "ultimo_anfir": _ultima_evidencia(anf_cliente),
            "ultimo_historico": _ultima_evidencia(hist_cliente),
            "ultimo_crm": _ultima_evidencia(crm_cliente),
        }
    direcionamento["regra_evidencia"] = "CLIENTE_EXATO_NORMALIZADO; ANFIR_2026 + HISTORICO_FUNIL_2026 + CRM_ATUAL; SEM_INFERENCIA_POR_DDD"
    return direcionamento


def _clientes_carteira_atual(responsavel_id: str) -> int:
    try:
        dados = (
            supabase.table("clientes")
            .select("id")
            .eq("responsavel_comercial_id", responsavel_id)
            .execute()
            .data
            or []
        )
        return len(dados)
    except Exception:
        return 0


def _clientes_anfir_unicos(registros: list[dict[str, Any]]) -> int:
    return len({_cliente_nome(item).upper() for item in registros if _cliente_nome(item)})


def _crm_2026(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in registros if _ano_registro(item) == 2026]


def _acao_regiao(mercado: int, crm_ativos: int, pipeline: float) -> tuple[str, str]:
    if mercado <= 0:
        return (
            "Não há unidades ANFIR 2026 atribuídas com responsabilidade comercial comprovada para este responsável.",
            "Revisar somente a atribuição cadastral dos clientes; não redistribuir mercado por DDD.",
        )
    if crm_ativos == 0:
        return (
            f"Há {mercado} unidade(s) de mercado atribuída(s) em 2026 e nenhuma negociação ativa de 2026 no CRM.",
            "Priorizar os clientes da carteira com presença ANFIR e abrir atuação apenas quando houver contato comercial real.",
        )
    densidade = crm_ativos / mercado
    if densidade < 0.05:
        return (
            f"O mercado atribuído é maior que a presença atual no CRM 2026: {crm_ativos} negócio(s) ativo(s) para {mercado} unidade(s) de mercado.",
            "Aumentar cobertura comercial dos clientes já pertencentes ao responsável, começando pelos que aparecem no mercado 2026 e ainda não têm negociação ativa.",
        )
    return (
        f"A carteira tem {crm_ativos} negócio(s) ativo(s) de 2026, somando R$ {pipeline:,.0f}, sobre {mercado} unidade(s) de mercado 2026.",
        "Concentrar acompanhamento nos negócios ativos e replicar a abordagem nos clientes do mesmo perfil que ainda não entraram no CRM.",
    )


def _regioes(
    alvo: UsuarioAutenticado | None,
    equipe: list[dict[str, Any]],
    mercado_total: list[dict[str, Any]],
    historico_escopo: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    crm_base = carregar_oportunidades_enriquecidas()
    registros = equipe if alvo is None else [item for item in equipe if str(item.get("id")) == str(alvo.id)]
    saida: list[dict[str, Any]] = []

    for registro in registros:
        responsavel = _usuario_regional(registro)
        anf = filtrar_anfir_por_responsavel_comercial(list(mercado_total), str(responsavel.id), responsavel.nome)
        crm = _crm_2026(_crm_carteira(responsavel, crm_base))
        historico = _historico_carteira(responsavel, historico_escopo or [])
        ativos = [item for item in crm if str(item.get("status") or "").upper() not in FECHADOS]
        serie = _serie_12()
        sem_mes = 0
        for item in anf:
            quantidade = _quantidade(item, 1)
            if not _somar_mes(serie, item, quantidade):
                sem_mes += quantidade
        mercado = sum(_quantidade(item, 1) for item in anf)
        clientes_carteira = _clientes_carteira_atual(str(responsavel.id))
        clientes_anfir = _clientes_anfir_unicos(anf)
        negociacoes_anfir = len(anf)
        pipeline = round(sum(_valor(item) for item in ativos), 2)
        leitura, acao = _acao_regiao(mercado, len(ativos), pipeline)

        clientes_com_crm_ativo = {_fold(_cliente_nome(item)) for item in ativos if _cliente_nome(item)}
        sem_crm = [item for item in anf if _cliente_nome(item) and _fold(_cliente_nome(item)) not in clientes_com_crm_ativo]
        base_direcionamento = sem_crm if sem_crm else anf
        rotulo = "Prioridade sem CRM ativo" if sem_crm else "Prioridade de acompanhamento"
        direcionamento = direcionar_registros(
            base_direcionamento,
            _quantidade,
            _linha_nome,
            responsavel_padrao=responsavel.nome,
            rotulo=rotulo,
        )
        direcionamento = _enriquecer_direcionamento(direcionamento, anf, historico, crm)
        if direcionamento["texto"]:
            acao = f'{acao} {direcionamento["texto"]}'

        saida.append({
            "id": responsavel.id,
            "nome": responsavel.nome,
            "codigo_regional": registro.get("codigo_regional"),
            "ddds": registro.get("ddds") or [],
            "mercado_2026": mercado,
            "clientes_mercado": clientes_anfir,
            "clientes_carteira": clientes_carteira,
            "clientes_anfir_2026": clientes_anfir,
            "negociacoes_anfir_2026": negociacoes_anfir,
            "crm_ativos": len(ativos),
            "crm_registros_2026": len(crm),
            "pipeline_ativo": pipeline,
            "mercado_mensal": serie,
            "registros_sem_mes": sem_mes,
            "regra_metricas": "MERCADO=UNIDADES_ANFIR_2026; CLIENTES=CLIENTES_UNICOS_ANFIR_2026; NEGOCIACOES=OCORRENCIAS_ANFIR_2026; CARTEIRA=RESPONSABILIDADE_ATUAL; CRM=OPORTUNIDADES_2026",
            "leitura_comercial": leitura,
            "acao_recomendada": acao,
            "direcionamento": direcionamento,
        })
    return sorted(saida, key=lambda item: (-int(item["mercado_2026"]), str(item["nome"])))


def _leitura_linha(nome: str, serie: list[int], total_real: int | None = None) -> tuple[str, str]:
    total = sum(serie) if total_real is None else total_real
    if total <= 0:
        return (
            f"Não há movimento ANFIR 2026 classificado com segurança para {nome} nesta seleção.",
            "Não forçar conclusão. Primeiro garantir classificação correta da linha nos registros ANFIR 2026.",
        )
    total_com_mes = sum(serie)
    if total_com_mes <= 0:
        return (
            f"{nome} soma {total} unidade(s) no mercado ANFIR 2026, mas não há competência mensal suficiente para afirmar pico, crescimento ou retração.",
            "Preservar o total da linha e qualificar a competência mensal antes de produzir leitura de tendência.",
        )
    pico = max(range(12), key=lambda i: serie[i])
    ultimo_mes = max(i for i, valor in enumerate(serie) if valor > 0)
    janela = serie[max(0, ultimo_mes - 2): ultimo_mes + 1]
    tendencia = "estável"
    if len(janela) >= 2 and janela[-1] > janela[0]:
        tendencia = "em alta"
    elif len(janela) >= 2 and janela[-1] < janela[0]:
        tendencia = "em queda"
    cobertura = "" if total_com_mes == total else f" A leitura mensal cobre {total_com_mes} de {total} unidade(s) com competência identificada."
    leitura = f"{nome} soma {total} unidade(s) no mercado ANFIR 2026; entre as unidades com mês informado, o maior volume ocorreu em {MESES[pico]} e a sequência mais recente está {tendencia}.{cobertura}"
    if tendencia == "em queda":
        acao = "Revisar os clientes desta linha com movimento no início do ano e queda recente, priorizando recuperação comercial antes de ampliar prospecção fria."
    elif tendencia == "em alta":
        acao = "Proteger a aceleração da linha: antecipar abordagem nos clientes de perfil semelhante aos que sustentaram o crescimento recente."
    else:
        acao = "Manter cadência sobre a base ANFIR 2026 e priorizar clientes da linha ainda sem captura comercial comprovada."
    return leitura, acao


def _linhas_2026(
    anfir: list[dict[str, Any]],
    historico: list[dict[str, Any]] | None = None,
    crm: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    series = {
        "Trailer": _serie_12(),
        "Diesel Truck": _serie_12(),
        "Direct Drive": _serie_12(),
        "Não classificado": _serie_12(),
    }
    itens_por_linha: dict[str, list[dict[str, Any]]] = {nome: [] for nome in series}
    sem_mes = 0
    for item in anfir:
        if _ano_registro(item) not in (None, 2026):
            continue
        linha = _linha_nome(item)
        itens_por_linha[linha].append(item)
        quantidade = _quantidade(item, 1)
        if not _somar_mes(series[linha], item, quantidade):
            sem_mes += quantidade

    blocos = []
    for chave, codigo in (("Trailer", "trailer"), ("Diesel Truck", "diesel_truck"), ("Direct Drive", "direct_drive")):
        registros_linha = itens_por_linha[chave]
        composicao = composicao_marca_linha(registros_linha)
        total_real = int(composicao["mercado"])
        leitura, acao = _leitura_linha(chave, series[chave], total_real)

        nao_capturados_carrier = [item for item in registros_linha if not _carrier_confirmado(item)]
        base_direcionamento = nao_capturados_carrier if nao_capturados_carrier else registros_linha
        rotulo = "Prioridade comercial fora da captura Carrier" if nao_capturados_carrier else "Prioridade de proteção Carrier"
        direcionamento = direcionar_registros(
            base_direcionamento,
            _quantidade,
            _linha_nome,
            rotulo=rotulo,
        )
        direcionamento = _enriquecer_direcionamento(direcionamento, registros_linha, historico, crm)
        if direcionamento["texto"]:
            acao = f'{acao} {direcionamento["texto"]}'

        blocos.append({
            "codigo": codigo,
            "nome": chave,
            "total_2026": total_real,
            "mensal": series[chave],
            "composicao_marca": composicao,
            "leitura_comercial": leitura,
            "acao_recomendada": acao,
            "direcionamento": direcionamento,
        })
    return {
        "meses": list(MESES),
        "linhas": blocos,
        "nao_classificado_2026": sum(_quantidade(item, 1) for item in itens_por_linha["Não classificado"]),
        "unidades_sem_mes": sem_mes,
        "fonte": "ANFIR_2026",
        "regra_calculo": "PRIMEIRO_LINHA_DEPOIS_MARCA; MESMO_DENOMINADOR; FECHAMENTO_100_PCT",
    }


def _eh_perda_anfir_2026(item: dict[str, Any]) -> bool:
    if _ano_registro(item) not in (None, 2026):
        return False
    return _fold(item.get("status")) in STATUS_PERDA_ANFIR_2026


def _acao_perda(motivos: Counter[str], linhas: Counter[str], total_perdido: int) -> tuple[str, str]:
    if total_perdido <= 0:
        return (
            "Não há perda comercial identificada no ANFIR 2026 nesta seleção.",
            "Manter disciplina de leitura do ANFIR e atuar assim que surgir perda ou ausência de captura comercial comprovada.",
        )
    if not motivos:
        return (
            f"Há {total_perdido} perda(s) no ANFIR 2026, mas sem motivo comercial estruturado.",
            "Qualificar os registros sem motivo antes de definir estratégia; sem causa comprovada, a recomendação seria especulativa.",
        )
    motivo, qtd = motivos.most_common(1)[0]
    linha = linhas.most_common(1)[0][0] if linhas else "linha não classificada"
    motivo_fold = _fold(motivo)
    if motivo_fold in {"OUTRO", "OUTROS", "SEM RETORNO", "SEM_RETORNO", "NAO INFORMADO", "NAO_INFORMADO"}:
        acao = "Revisar primeiro os casos com motivo genérico e registrar a causa comercial real; sem isso, não há plano de reversão auditável."
    elif "PRECO" in motivo_fold:
        acao = "Revisar os casos de preço por produto e cliente, separar desconto de percepção de valor e preparar defesa comercial Carrier antes da próxima proposta."
    elif "NAO PARTICIPAMOS" in motivo_fold:
        acao = "Atacar cobertura: identificar os clientes em que não participamos da proposta e criar cadência comercial antes da próxima compra ou implementação."
    elif "RELACIONAMENTO" in motivo_fold:
        acao = "Priorizar recuperação de relacionamento nos clientes afetados, com responsável definido e próxima ação objetiva antes da próxima decisão de compra."
    elif "SOLUCAO TECNICA" in motivo_fold:
        acao = "Separar as perdas sem solução técnica por linha e aplicação e levar os casos recorrentes para tratamento técnico-comercial Carrier."
    elif "CONCOR" in motivo_fold:
        acao = "Mapear qual concorrente venceu, por linha e cliente, e preparar abordagem de recuperação específica nos casos de maior recorrência."
    else:
        acao = "Atacar primeiro o motivo dominante com plano por cliente e linha; medir no ANFIR seguinte se a incidência do mesmo motivo começa a cair."
    return (
        f"No ANFIR 2026, o motivo mais frequente é {motivo} ({qtd} unidade(s)); a maior concentração por linha está em {linha}.",
        acao,
    )


def _perdas_2026(
    anfir: list[dict[str, Any]],
    historico: list[dict[str, Any]] | None = None,
    crm: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    perdidos = [item for item in anfir if _eh_perda_anfir_2026(item)]
    motivos: Counter[str] = Counter()
    linhas: Counter[str] = Counter()
    mensal = _serie_12()
    sem_mes = 0
    total_perdido = 0
    total_com_motivo = 0
    for item in perdidos:
        quantidade = _quantidade(item, 1)
        total_perdido += quantidade
        motivo = str(item.get("motivo") or "").strip()
        if motivo:
            motivos[motivo] += quantidade
            total_com_motivo += quantidade
        linhas[_linha_nome(item)] += quantidade
        if not _somar_mes(mensal, item, quantidade):
            sem_mes += quantidade
    leitura, acao = _acao_perda(motivos, linhas, total_perdido)
    motivo_dominante = motivos.most_common(1)[0][0] if motivos else None
    direcionamento = direcionar_perda_dominante(
        perdidos,
        motivo_dominante,
        _quantidade,
        _linha_nome,
    )
    direcionamento = _enriquecer_direcionamento(direcionamento, perdidos, historico, crm)
    if direcionamento["texto"]:
        acao = f'{acao} {direcionamento["texto"]}'
    return {
        "ano": 2026,
        "fonte": "ANFIR_2026",
        "fontes_decisao": ["ANFIR_2026", "HISTORICO_FUNIL_2026", "CRM_ATUAL"],
        "total_perdido": total_perdido,
        "total_com_motivo": total_com_motivo,
        "motivos": [{"nome": nome, "quantidade": qtd} for nome, qtd in motivos.most_common(10)],
        "por_linha": [{"nome": nome, "quantidade": qtd} for nome, qtd in linhas.most_common()],
        "mensal": mensal,
        "registros_sem_mes": sem_mes,
        "leitura_comercial": leitura,
        "acao_recomendada": acao,
        "direcionamento": direcionamento,
    }


@router.get("/insights")
def insights_mapa(
    responsavel_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    alvo, equipe = _resolver_alvo(usuario, responsavel_id)
    mercado_total = _mercado_anfir_2026()
    anfir_escopo = _anfir_do_escopo(alvo, equipe, mercado_total)
    historico_escopo, crm_escopo = _fontes_do_escopo(alvo, equipe)
    consolidado = _pode_gerir(usuario)

    return {
        "ano": 2026,
        "meses": list(MESES),
        "escopo": {
            "consolidado": consolidado,
            "modo": "TODA_EQUIPE" if alvo is None else "RESPONSAVEL",
            "responsavel_id": None if alvo is None else alvo.id,
            "responsavel_nome": "Toda a equipe comercial" if alvo is None else alvo.nome,
            "regra": "MASTER_GESTAO_PODE_CONSOLIDAR; DEMAIS_USUARIOS_SEMPRE_RECEBEM_APENAS_O_PROPRIO_LOGIN",
        },
        "regioes": _regioes(alvo, equipe, mercado_total, historico_escopo),
        "linhas_2026": _linhas_2026(anfir_escopo, historico_escopo, crm_escopo),
        "perdas": _perdas_2026(anfir_escopo, historico_escopo, crm_escopo),
    }
