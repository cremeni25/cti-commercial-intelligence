from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers import strategic_layers_router as estrategia
from routers.crm_scope_estrategia_router import FECHADOS
from routers.crm_scope_mapa_equipe_router import (
    _crm_carteira,
    _deduplicar,
    _historico_carteira,
    _pode_gerir,
    _resolver_alvo,
    _usuario_regional,
)
from services.commercial_client_scope import filtrar_anfir_por_responsavel_comercial
from services.crm_live_projection import carregar_oportunidades_enriquecidas
from services.historical_commercial_source import carregar_historico_comercial
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


def _ano_registro(item: dict[str, Any]) -> int | None:
    valor = item.get("ano")
    try:
        if valor not in (None, ""):
            ano = int(float(valor))
            if 2000 <= ano <= 2100:
                return ano
    except (TypeError, ValueError):
        pass

    for campo in ("data", "data_evento", "data_negociacao", "created_at", "updated_at"):
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

    for campo in ("data", "data_evento", "data_negociacao", "created_at", "updated_at"):
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


def _serie_12() -> list[int]:
    return [0 for _ in range(12)]


def _somar_mes(serie: list[int], item: dict[str, Any], valor: int = 1) -> bool:
    mes = _mes_registro(item)
    if not mes:
        return False
    serie[mes - 1] += max(0, valor)
    return True


def _historico_do_escopo(alvo: UsuarioAutenticado | None, equipe: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base = [item for item in carregar_historico_comercial() if _ano_registro(item) == 2026]
    if alvo is not None:
        return _historico_carteira(alvo, base)

    todos: list[dict[str, Any]] = []
    for registro in equipe:
        todos.extend(_historico_carteira(_usuario_regional(registro), base))
    return _deduplicar(todos)


def _mercado_anfir_2026() -> list[dict[str, Any]]:
    mercado_total, _, _ = estrategia._anfir(
        "viena-sp",
        "PERSONALIZADO",
        None,
        None,
        date(2026, 1, 1),
        date(2026, 12, 31),
    )
    return list(mercado_total)


def _anfir_do_escopo(alvo: UsuarioAutenticado | None, equipe: list[dict[str, Any]], mercado_total: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if alvo is not None:
        return filtrar_anfir_por_responsavel_comercial(list(mercado_total), str(alvo.id), alvo.nome)

    todos: list[dict[str, Any]] = []
    for registro in equipe:
        responsavel = _usuario_regional(registro)
        todos.extend(filtrar_anfir_por_responsavel_comercial(list(mercado_total), str(responsavel.id), responsavel.nome))
    return _deduplicar(todos)


def _acao_regiao(mercado: int, crm_ativos: int, pipeline: float) -> tuple[str, str]:
    if mercado <= 0:
        return (
            "Não há mercado 2026 atribuído com responsabilidade comercial comprovada para este responsável.",
            "Revisar somente a atribuição cadastral dos clientes; não redistribuir mercado por DDD.",
        )
    if crm_ativos == 0:
        return (
            f"Há {mercado} registros de mercado atribuídos em 2026 e nenhuma negociação ativa no CRM.",
            "Priorizar os clientes de maior recorrência/volume desta carteira e abrir atuação apenas quando houver contato comercial real.",
        )
    densidade = crm_ativos / mercado
    if densidade < 0.05:
        return (
            f"O mercado atribuído é maior que a presença atual no CRM: {crm_ativos} negócio(s) ativo(s) para {mercado} registros de mercado.",
            "Aumentar cobertura comercial dos clientes já pertencentes ao responsável, começando pelos que aparecem no mercado 2026 e ainda não têm negociação ativa.",
        )
    return (
        f"A carteira tem {crm_ativos} negócio(s) ativo(s), somando R$ {pipeline:,.0f}, sobre {mercado} registros de mercado 2026.",
        "Concentrar acompanhamento nos negócios ativos e replicar a abordagem nos clientes do mesmo perfil que ainda não entraram no CRM.",
    )


def _regioes(alvo: UsuarioAutenticado | None, equipe: list[dict[str, Any]], mercado_total: list[dict[str, Any]]) -> list[dict[str, Any]]:
    crm_base = carregar_oportunidades_enriquecidas()
    registros = equipe if alvo is None else [item for item in equipe if str(item.get("id")) == str(alvo.id)]
    saida: list[dict[str, Any]] = []

    for registro in registros:
        responsavel = _usuario_regional(registro)
        anf = filtrar_anfir_por_responsavel_comercial(list(mercado_total), str(responsavel.id), responsavel.nome)
        crm = _crm_carteira(responsavel, crm_base)
        ativos = [item for item in crm if str(item.get("status") or "").upper() not in FECHADOS]
        serie = _serie_12()
        sem_mes = 0
        for item in anf:
            if not _somar_mes(serie, item, 1):
                sem_mes += 1
        mercado = len(anf)
        pipeline = round(sum(_valor(item) for item in ativos), 2)
        leitura, acao = _acao_regiao(mercado, len(ativos), pipeline)
        saida.append({
            "id": responsavel.id,
            "nome": responsavel.nome,
            "codigo_regional": registro.get("codigo_regional"),
            "ddds": registro.get("ddds") or [],
            "mercado_2026": mercado,
            "clientes_mercado": len({
                str(item.get("cliente") or item.get("empresa") or item.get("transportadora") or "").strip().upper()
                for item in anf
                if str(item.get("cliente") or item.get("empresa") or item.get("transportadora") or "").strip()
            }),
            "crm_ativos": len(ativos),
            "pipeline_ativo": pipeline,
            "mercado_mensal": serie,
            "registros_sem_mes": sem_mes,
            "leitura_comercial": leitura,
            "acao_recomendada": acao,
        })
    return sorted(saida, key=lambda item: (-int(item["mercado_2026"]), str(item["nome"])))


def _leitura_linha(nome: str, serie: list[int]) -> tuple[str, str]:
    total = sum(serie)
    if total <= 0:
        return (
            f"Não há movimento 2026 classificado com segurança para {nome} nesta seleção.",
            "Não forçar conclusão. Primeiro garantir classificação correta da linha nos registros 2026.",
        )
    pico = max(range(12), key=lambda i: serie[i])
    ultimo_mes = max((i for i, valor in enumerate(serie) if valor > 0), default=0)
    janela = serie[max(0, ultimo_mes - 2): ultimo_mes + 1]
    tendencia = "estável"
    if len(janela) >= 2 and janela[-1] > janela[0]:
        tendencia = "em alta"
    elif len(janela) >= 2 and janela[-1] < janela[0]:
        tendencia = "em queda"
    leitura = f"{nome} soma {total} unidade(s) no movimento comercial 2026; o maior volume ocorreu em {MESES[pico]} e a sequência mais recente está {tendencia}."
    if tendencia == "em queda":
        acao = "Revisar clientes que compraram ou negociaram esta linha no início do ano e estão sem movimento recente; priorizar recuperação antes de ampliar prospecção fria."
    elif tendencia == "em alta":
        acao = "Proteger a aceleração: antecipar follow-up dos negócios atuais e buscar clientes com perfil semelhante aos que geraram o crescimento recente."
    else:
        acao = "Manter cadência sobre a base ativa e identificar clientes 2026 ainda sem abordagem para ampliar participação sem dispersar esforço."
    return leitura, acao


def _linhas_2026(historico: list[dict[str, Any]]) -> dict[str, Any]:
    series = {
        "Trailer": _serie_12(),
        "Diesel Truck": _serie_12(),
        "Direct Drive": _serie_12(),
        "Não classificado": _serie_12(),
    }
    sem_mes = 0
    for item in historico:
        linha = _linha_nome(item)
        quantidade = _quantidade(item, 1)
        if not _somar_mes(series[linha], item, quantidade):
            sem_mes += quantidade

    blocos = []
    for chave, codigo in (("Trailer", "trailer"), ("Diesel Truck", "diesel_truck"), ("Direct Drive", "direct_drive")):
        leitura, acao = _leitura_linha(chave, series[chave])
        blocos.append({
            "codigo": codigo,
            "nome": chave,
            "total_2026": sum(series[chave]),
            "mensal": series[chave],
            "leitura_comercial": leitura,
            "acao_recomendada": acao,
        })
    return {
        "meses": list(MESES),
        "linhas": blocos,
        "nao_classificado_2026": sum(series["Não classificado"]),
        "unidades_sem_mes": sem_mes,
        "fonte": "HISTORICO_FUNIL_2026",
    }


def _acao_perda(motivos: Counter[str], linhas: Counter[str], total_perdido: int) -> tuple[str, str]:
    if total_perdido <= 0:
        return (
            "Não há perda 2026 registrada com status PERDIDO nesta seleção.",
            "Manter disciplina de encerramento no CRM/Funil para que toda perda futura tenha motivo comercial registrado.",
        )
    if not motivos:
        return (
            f"Há {total_perdido} perda(s) em 2026, mas os motivos não estão estruturados.",
            "A primeira ação é qualificar o encerramento das perdas; sem motivo confiável, qualquer estratégia de reversão seria especulativa.",
        )
    motivo, qtd = motivos.most_common(1)[0]
    linha = linhas.most_common(1)[0][0] if linhas else "linha não classificada"
    motivo_fold = _fold(motivo)
    if motivo_fold in {"OUTRO", "SEM RETORNO", "SEM_RETORNO", "NAO INFORMADO", "NAO_INFORMADO"}:
        acao = "Reabrir a leitura dos casos encerrados como genéricos e capturar o motivo comercial real. Em paralelo, estabelecer follow-up obrigatório antes de classificar uma negociação como sem retorno."
    elif "PRECO" in motivo_fold:
        acao = "Revisar os casos de preço por produto e cliente, separar desconto de percepção de valor e preparar defesa comercial Carrier antes da próxima proposta."
    elif "CONCOR" in motivo_fold:
        acao = "Mapear qual concorrente venceu, por qual linha e argumento, e preparar abordagem de recuperação específica para os clientes afetados."
    else:
        acao = "Atacar primeiro o motivo dominante com plano por cliente e linha; medir nas próximas negociações se a incidência do mesmo motivo começa a cair."
    return (
        f"Em 2026, o motivo mais frequente é {motivo.replace('_', ' ')} ({qtd} caso(s)); a maior concentração por linha está em {linha}.",
        acao,
    )


def _perdas_2026(historico: list[dict[str, Any]]) -> dict[str, Any]:
    perdidos = [item for item in historico if _fold(item.get("status")) == "PERDIDO"]
    motivos = Counter(
        str(item.get("motivo_perda") or "").strip().upper()
        for item in perdidos
        if str(item.get("motivo_perda") or "").strip()
    )
    linhas = Counter(_linha_nome(item) for item in perdidos)
    mensal = _serie_12()
    sem_mes = 0
    for item in perdidos:
        if not _somar_mes(mensal, item, 1):
            sem_mes += 1
    leitura, acao = _acao_perda(motivos, linhas, len(perdidos))
    return {
        "ano": 2026,
        "total_perdido": len(perdidos),
        "total_com_motivo": sum(motivos.values()),
        "motivos": [{"nome": nome, "quantidade": qtd} for nome, qtd in motivos.most_common(10)],
        "por_linha": [{"nome": nome, "quantidade": qtd} for nome, qtd in linhas.most_common()],
        "mensal": mensal,
        "registros_sem_mes": sem_mes,
        "leitura_comercial": leitura,
        "acao_recomendada": acao,
    }


@router.get("/insights")
def insights_mapa(
    responsavel_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    alvo, equipe = _resolver_alvo(usuario, responsavel_id)
    historico = _historico_do_escopo(alvo, equipe)
    mercado_total = _mercado_anfir_2026()
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
        "regioes": _regioes(alvo, equipe, mercado_total),
        "linhas_2026": _linhas_2026(historico),
        "perdas": _perdas_2026(historico),
    }
