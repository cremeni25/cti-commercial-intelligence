from __future__ import annotations

import unicodedata
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Callable

from core.supabase_client import supabase

GANHOS = {"GANHO", "GANHA", "WON"}
FECHADOS = {"GANHO", "GANHA", "WON", "PERDIDO", "PERDIDA", "LOST", "CANCELADO", "CANCELADA", "CONCLUIDO", "CONCLUIDA"}
CONCLUIDAS = {"CONCLUIDA", "CONCLUÍDA", "CONCLUIDO", "CONCLUÍDO"}
PRIORIDADE_CICLO = {
    "NOVO_SINAL": 0,
    "ESTAGNADO": 1,
    "ACAO_NECESSARIA": 2,
    "EM_ACOMPANHAMENTO": 3,
    "CONVERTIDO": 4,
}


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")


def _texto(item: dict[str, Any], *campos: str) -> str:
    for campo in campos:
        valor = str(item.get(campo) or "").strip()
        if valor:
            return valor
    return ""


def _data_registro(item: dict[str, Any]) -> date | None:
    for campo in ("data", "updated_at", "created_at", "data_abertura", "data_evento"):
        bruto = str(item.get(campo) or "").strip()
        if not bruto:
            continue
        try:
            return datetime.fromisoformat(bruto.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return date.fromisoformat(bruto[:10])
            except ValueError:
                continue
    return None


def _iso(valor: date | None) -> str | None:
    return valor.isoformat() if valor else None


def _resolver_clientes(alvos: list[dict[str, Any]]) -> dict[str, list[str]]:
    nomes = sorted({_texto(item, "cliente") for item in alvos if _texto(item, "cliente")})
    if not nomes:
        return {}
    por_nome: dict[str, list[str]] = defaultdict(list)
    try:
        registros = supabase.table("clientes").select("id,nome").in_("nome", nomes).execute().data or []
        for item in registros:
            nome = _fold(item.get("nome"))
            identificador = str(item.get("id") or "").strip()
            if nome and identificador:
                por_nome[nome].append(identificador)
    except Exception:
        pass
    try:
        registros = supabase.table("cti_clientes").select("id,cliente").in_("cliente", nomes).execute().data or []
        for item in registros:
            nome = _fold(item.get("cliente"))
            identificador = str(item.get("id") or "").strip()
            if nome and identificador and identificador not in por_nome[nome]:
                por_nome[nome].append(identificador)
    except Exception:
        pass
    return dict(por_nome)


def _resolver_responsaveis(alvos: list[dict[str, Any]]) -> dict[str, str]:
    nomes = sorted({_texto(item, "responsavel") for item in alvos if _texto(item, "responsavel") and _texto(item, "responsavel") != "Responsável não informado"})
    if not nomes:
        return {}
    try:
        registros = supabase.table("cti_users").select("id,nome").in_("nome", nomes).execute().data or []
    except Exception:
        return {}
    return {
        _fold(item.get("nome")): str(item.get("id") or "")
        for item in registros
        if item.get("id") and item.get("nome")
    }


def _carregar_movimentos(ids_clientes: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not ids_clientes:
        return [], []
    oportunidades: list[dict[str, Any]] = []
    atividades: list[dict[str, Any]] = []
    try:
        oportunidades = supabase.table("cti_oportunidades").select("id,cliente_id,responsavel_id,status,created_at,updated_at").in_("cliente_id", ids_clientes).execute().data or []
    except Exception:
        oportunidades = []
    try:
        atividades = supabase.table("cti_atividades").select("id,cliente_id,usuario_id,status,tipo,titulo,descricao,data,created_at,updated_at").in_("cliente_id", ids_clientes).execute().data or []
    except Exception:
        atividades = []
    return oportunidades, atividades


def _ciclo_cliente(
    alvo: dict[str, Any],
    ids_cliente: list[str],
    responsavel_id: str | None,
    oportunidades: list[dict[str, Any]],
    atividades: list[dict[str, Any]],
) -> dict[str, Any]:
    ids = set(ids_cliente)
    opp = [item for item in oportunidades if str(item.get("cliente_id") or "") in ids]
    acts = [item for item in atividades if str(item.get("cliente_id") or "") in ids]
    if responsavel_id:
        opp = [item for item in opp if not item.get("responsavel_id") or str(item.get("responsavel_id")) == responsavel_id]
        acts = [item for item in acts if not item.get("usuario_id") or str(item.get("usuario_id")) == responsavel_id]

    hoje = datetime.now(timezone.utc).date()
    ganhos = [item for item in opp if _fold(item.get("status")) in GANHOS]
    ativos = [item for item in opp if _fold(item.get("status")) not in FECHADOS]
    pendentes = [item for item in acts if _fold(item.get("status")) not in CONCLUIDAS]
    futuras = [item for item in pendentes if (_data_registro(item) or date.min) >= hoje]
    datas = [valor for item in [*opp, *acts] if (valor := _data_registro(item))]
    ultima = max(datas) if datas else None
    proxima = min((_data_registro(item) for item in futuras if _data_registro(item)), default=None)
    dias_sem_movimento = (hoje - ultima).days if ultima else None

    if ganhos:
        estado = "CONVERTIDO"
        rotulo = "Convertido"
        leitura = "Há oportunidade ganha registrada no CRM para este cliente. O caso deixa a fila de recuperação e permanece apenas em proteção e próxima janela comercial."
        acao = "Preservar o relacionamento, registrar o resultado e acompanhar a próxima oportunidade sem manter este cliente como prioridade de recuperação."
    elif ativos and not futuras and dias_sem_movimento is not None and dias_sem_movimento >= 21:
        estado = "ESTAGNADO"
        rotulo = "Acompanhamento estagnado"
        leitura = f"Há {len(ativos)} oportunidade(s) ativa(s), porém sem próxima atividade futura e sem movimentação registrada há {dias_sem_movimento} dia(s)."
        acao = "Retomar a negociação, registrar o motivo da estagnação e definir uma próxima ação com data; se necessário, escalar ao gestor."
    elif ativos or futuras:
        estado = "EM_ACOMPANHAMENTO"
        rotulo = "Em acompanhamento"
        detalhe = f"Há {len(ativos)} oportunidade(s) ativa(s)" if ativos else "Há atividade comercial programada"
        if proxima:
            detalhe += f" e próxima ação prevista para {proxima.isoformat()}"
        leitura = detalhe + ". O cliente continua monitorado, mas já possui cobertura comercial em andamento."
        acao = "Cumprir a próxima ação registrada e atualizar o CRM com o resultado para que a prioridade seja recalculada automaticamente."
    elif acts:
        estado = "ACAO_NECESSARIA"
        rotulo = "Próxima ação necessária"
        leitura = "Já existe atividade registrada para este cliente, mas não há oportunidade ativa nem próxima atividade futura. O acompanhamento não deve ser considerado concluído por ausência de próximo passo."
        acao = "Registrar a próxima ação comercial ou encerrar o caso com motivo qualificado; enquanto isso, o cliente permanece na fila de atenção."
    else:
        estado = "NOVO_SINAL"
        rotulo = "Novo sinal"
        leitura = "O mercado gerou um sinal comercial para este cliente e ainda não há atividade nem oportunidade CRM vinculada ao mesmo responsável."
        acao = "Fazer a primeira abordagem, registrar a interação no CRM e definir a próxima ação com data."

    return {
        "estado": estado,
        "rotulo": rotulo,
        "prioridade": PRIORIDADE_CICLO[estado],
        "oportunidades": len(opp),
        "oportunidades_ativas": len(ativos),
        "ganhos": len(ganhos),
        "atividades": len(acts),
        "atividades_pendentes": len(pendentes),
        "ultima_movimentacao": _iso(ultima),
        "proxima_atividade": _iso(proxima),
        "dias_sem_movimento": dias_sem_movimento,
        "leitura": leitura,
        "acao": acao,
    }


def _aplicar_ciclo_comercial(alvos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not alvos:
        return alvos
    clientes = _resolver_clientes(alvos)
    responsaveis = _resolver_responsaveis(alvos)
    todos_ids = sorted({identificador for ids in clientes.values() for identificador in ids})
    oportunidades, atividades = _carregar_movimentos(todos_ids)
    for alvo in alvos:
        chave_cliente = _fold(alvo.get("cliente"))
        responsavel_id = responsaveis.get(_fold(alvo.get("responsavel")))
        ciclo = _ciclo_cliente(
            alvo,
            clientes.get(chave_cliente, []),
            responsavel_id,
            oportunidades,
            atividades,
        )
        alvo["ciclo_comercial"] = ciclo
        alvo["leitura_ciclo"] = ciclo["leitura"]
        alvo["acao_ciclo"] = ciclo["acao"]
    return alvos


def direcionar_registros(
    registros: list[dict[str, Any]],
    quantidade_fn: Callable[[dict[str, Any], int], int],
    linha_fn: Callable[[dict[str, Any]], str],
    limite: int = 5,
    responsavel_padrao: str | None = None,
    rotulo: str = "Quem deve agir / para quem",
) -> dict[str, Any]:
    """Agrupa evidências por responsável + cliente e renova o ranking conforme o ciclo CRM."""
    agrupados: dict[tuple[str, str], dict[str, Any]] = {}

    for item in registros:
        cliente = _texto(item, "cliente", "empresa", "transportadora") or "Cliente não identificado"
        responsavel = responsavel_padrao or _texto(
            item,
            "responsavel",
            "responsável",
            "representante_atual",
            "representante_original",
            "vendedor",
            "consultor",
        ) or "Responsável não informado"
        chave = (_fold(responsavel), _fold(cliente))
        if chave not in agrupados:
            agrupados[chave] = {
                "responsavel": responsavel,
                "cliente": cliente,
                "unidades": 0,
                "ocorrencias": 0,
                "linhas": defaultdict(int),
            }
        grupo = agrupados[chave]
        quantidade = quantidade_fn(item, 1)
        grupo["unidades"] += quantidade
        grupo["ocorrencias"] += 1
        grupo["linhas"][linha_fn(item)] += quantidade

    alvos: list[dict[str, Any]] = []
    for grupo in agrupados.values():
        linhas = sorted(grupo.pop("linhas").items(), key=lambda par: (-par[1], par[0]))
        grupo["linha_principal"] = linhas[0][0] if linhas else "Não classificado"
        alvos.append(grupo)

    _aplicar_ciclo_comercial(alvos)
    alvos.sort(
        key=lambda item: (
            int((item.get("ciclo_comercial") or {}).get("prioridade", 99)),
            -int(item["unidades"]),
            str(item["responsavel"]),
            str(item["cliente"]),
        )
    )
    alvos = alvos[: max(1, limite)]
    partes = [
        f'{item["responsavel"]} → {item["cliente"]} '
        f'({item["unidades"]} un.; {item["ocorrencias"]} ocorrência(s); {item["linha_principal"]}; {(item.get("ciclo_comercial") or {}).get("rotulo", "sem ciclo")})'
        for item in alvos
    ]
    texto = f"{rotulo}: " + "; ".join(partes) + "." if partes else ""
    return {
        "alvos": alvos,
        "texto": texto,
        "regra_ranking": "CICLO_CRM_DETERMINISTICO; NOVO_SINAL>ESTAGNADO>ACAO_NECESSARIA>EM_ACOMPANHAMENTO>CONVERTIDO; DESEMPATE_POR_UNIDADES",
    }


def direcionar_perda_dominante(
    perdidos: list[dict[str, Any]],
    motivo_dominante: str | None,
    quantidade_fn: Callable[[dict[str, Any], int], int],
    linha_fn: Callable[[dict[str, Any]], str],
    limite: int = 5,
) -> dict[str, Any]:
    """Transforma a causa dominante de perda em alvo comercial auditável."""
    if not motivo_dominante:
        return {"motivo": None, "alvos": [], "texto": ""}

    alvo_fold = _fold(motivo_dominante)
    filtrados = [item for item in perdidos if _fold(_texto(item, "motivo")) == alvo_fold]
    direcionamento = direcionar_registros(
        filtrados,
        quantidade_fn,
        linha_fn,
        limite=limite,
        rotulo="Quem deve agir / para quem",
    )
    return {
        "motivo": motivo_dominante,
        "alvos": direcionamento["alvos"],
        "texto": direcionamento["texto"],
        "regra_ranking": direcionamento.get("regra_ranking"),
    }
