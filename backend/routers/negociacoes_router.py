from collections import Counter
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase

router = APIRouter()
ETAPAS_PIPELINE = [
    "OPORTUNIDADE",
    "ATIVIDADES",
    "PROPOSTA",
    "NEGOCIACAO",
    "PEDIDO",
    "GANHO",
    "PERDIDO",
]
TITULOS_GENERICOS = {"", "PROPOSTA COMERCIAL", "OPORTUNIDADE", "NOVA OPORTUNIDADE", "OPORTUNIDADE SEM TÍTULO"}
PREFIXO_TIPO_OPORTUNIDADE = "TIPO DA OPORTUNIDADE:"


class Negociacao(BaseModel):
    cliente: str
    cidade: str | None = None
    estado: str | None = None
    produto: str | None = None
    valor: float | None = None
    status: str | None = None


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _lista(tabela: str, ordem: str = "created_at") -> list[dict[str, Any]]:
    try:
        return supabase.table(tabela).select("*").order(ordem, desc=True).execute().data or []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao consultar {tabela}: {exc}") from exc


def _registro_operacional(registro: dict[str, Any]) -> bool:
    return not bool(registro.get("registro_teste")) and not bool(registro.get("arquivado_em"))


def _oportunidades_comerciais() -> list[dict[str, Any]]:
    """Retorna apenas oportunidades operacionais do núcleo comercial.

    Registros de teste e registros arquivados continuam preservados no banco e
    podem ser abertos por ID para homologação, mas não entram em quadro ou agenda.
    """
    return [item for item in _lista("cti_oportunidades") if _registro_operacional(item)]


def _fator_probabilidade(valor: Any) -> float:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return 0
    if numero <= 0:
        return 0
    return min(numero if numero <= 1 else numero / 100, 1)


def _data_iso(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return None


def _situacao_atividade(atividade: dict[str, Any], hoje: date | None = None) -> str:
    status = str(atividade.get("status") or "PENDENTE").upper()
    if status in {"CONCLUIDA", "CONCLUÍDA", "CANCELADA"}:
        return "CONCLUIDA" if status != "CANCELADA" else "CANCELADA"
    referencia = hoje or datetime.now(timezone.utc).date()
    data_atividade = _data_iso(atividade.get("data"))
    if not data_atividade:
        return "SEM_DATA"
    if data_atividade < referencia:
        return "ATRASADA"
    if data_atividade == referencia:
        return "HOJE"
    return "FUTURA"


def _titulo_oportunidade(oportunidade: dict[str, Any]) -> str:
    titulo = _texto(oportunidade.get("titulo"))
    if titulo.upper() not in TITULOS_GENERICOS:
        return titulo
    descricao = _texto(oportunidade.get("descricao"))
    for linha in descricao.splitlines():
        limpa = linha.strip()
        if limpa.upper().startswith(PREFIXO_TIPO_OPORTUNIDADE):
            tipo = limpa.split(":", 1)[1].strip()
            if tipo:
                return tipo
    return "Oportunidade comercial"


def _nome_cliente(cliente_id: Any) -> str:
    identificador = _texto(cliente_id)
    if not identificador:
        return ""
    for tabela in ("cti_clientes", "clientes"):
        try:
            dados = (
                supabase.table(tabela)
                .select("*")
                .eq("id", identificador)
                .limit(1)
                .execute()
                .data
                or []
            )
        except Exception:
            continue
        if not dados:
            continue
        cliente = dados[0]
        nome = _texto(
            cliente.get("razao_social")
            or cliente.get("nome_fantasia")
            or cliente.get("nome")
            or cliente.get("empresa")
            or cliente.get("cliente")
        )
        if nome:
            return nome
    return ""


def _consultar_oportunidade(tabela: str, oportunidade_id: str) -> list[dict[str, Any]]:
    return (
        supabase.table(tabela)
        .select("*")
        .eq("oportunidade_id", oportunidade_id)
        .execute()
        .data
        or []
    )


def _pedidos_da_oportunidade(
    propostas: list[dict[str, Any]],
    itens: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    proposta_ids = {_texto(item.get("id")) for item in propostas if item.get("id")}
    item_ids = {_texto(item.get("id")) for item in itens if item.get("id")}
    if not proposta_ids and not item_ids:
        return []

    encontrados: dict[str, dict[str, Any]] = {}

    def adicionar(registros: list[dict[str, Any]]) -> None:
        for registro in registros:
            chave = _texto(registro.get("id"))
            if chave:
                encontrados[chave] = registro

    if proposta_ids:
        ids = list(proposta_ids)
        adicionar(supabase.table("cti_pedidos").select("*").in_("proposta_id", ids).execute().data or [])
        adicionar(supabase.table("cti_pedidos").select("*").in_("proposta_aceita_id", ids).execute().data or [])
    if item_ids:
        adicionar(supabase.table("cti_pedidos").select("*").in_("item_oportunidade_id", list(item_ids)).execute().data or [])

    return list(encontrados.values())


def _evento(tipo: str, registro: dict[str, Any]) -> dict[str, Any]:
    return {
        "tipo": tipo,
        "data_hora": registro.get("updated_at") or registro.get("created_at") or registro.get("data") or registro.get("data_pedido"),
        "titulo": registro.get("titulo") or registro.get("descricao") or registro.get("numero") or tipo.title(),
        "status": registro.get("status_documento") or registro.get("status") or registro.get("nova_etapa") or registro.get("etapa"),
        "responsavel_id": registro.get("usuario_id") or registro.get("responsavel_id"),
        "registro": registro,
    }


@router.post("/negociacoes")
def criar_negociacao(negociacao: Negociacao):
    try:
        return supabase.table("negociacoes").insert(negociacao.model_dump()).execute().data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/negociacoes")
def listar_negociacoes():
    return _lista("negociacoes")


@router.get("/crm/pipeline/quadro")
def quadro_pipeline():
    """Retorna a fotografia comercial única usada pelo CTI e pelo CRM App."""
    oportunidades = _oportunidades_comerciais()
    oportunidades_ids = {item.get("id") for item in oportunidades if item.get("id")}
    movimentacoes = [
        movimento
        for movimento in _lista("cti_pipeline")
        if movimento.get("oportunidade_id") in oportunidades_ids and _registro_operacional(movimento)
    ]

    ultima_movimentacao: dict[str, dict[str, Any]] = {}
    for movimento in movimentacoes:
        oportunidade_id = movimento.get("oportunidade_id")
        if oportunidade_id and oportunidade_id not in ultima_movimentacao:
            ultima_movimentacao[oportunidade_id] = movimento

    cards = []
    for oportunidade in oportunidades:
        oportunidade_id = oportunidade.get("id")
        movimento = ultima_movimentacao.get(oportunidade_id, {})
        etapa = (
            movimento.get("nova_etapa")
            or movimento.get("etapa")
            or oportunidade.get("status")
            or "OPORTUNIDADE"
        ).upper()
        if etapa not in ETAPAS_PIPELINE:
            etapa = "OPORTUNIDADE"

        valor = float(oportunidade.get("valor_estimado") or 0)
        probabilidade = _fator_probabilidade(oportunidade.get("probabilidade"))
        cards.append({
            "id": oportunidade_id,
            "oportunidade_id": oportunidade_id,
            "titulo": _titulo_oportunidade(oportunidade),
            "cliente_id": oportunidade.get("cliente_id"),
            "responsavel_id": oportunidade.get("responsavel_id"),
            "etapa": etapa,
            "valor_estimado": valor,
            "probabilidade": probabilidade,
            "valor_ponderado": round(valor * probabilidade, 2),
            "equipamento": oportunidade.get("equipamento") or oportunidade.get("linha_equipamentos"),
            "implementadora": oportunidade.get("implementadora"),
            "municipio": oportunidade.get("municipio"),
            "estado": oportunidade.get("estado"),
            "data_fechamento_prevista": oportunidade.get("data_fechamento_prevista"),
            "ultima_movimentacao": movimento.get("created_at") or movimento.get("updated_at") or oportunidade.get("updated_at") or oportunidade.get("created_at"),
            "origem": oportunidade.get("origem"),
        })

    contagem = Counter(card["etapa"] for card in cards)
    valor_total = sum(card["valor_estimado"] for card in cards)
    valor_ponderado = sum(card["valor_ponderado"] for card in cards)

    return {
        "etapas": ETAPAS_PIPELINE,
        "cards": cards,
        "resumo": {
            "total_oportunidades": len(cards),
            "valor_total": round(valor_total, 2),
            "valor_ponderado": round(valor_ponderado, 2),
            "por_etapa": {etapa: contagem.get(etapa, 0) for etapa in ETAPAS_PIPELINE},
        },
    }


@router.get("/crm/agenda")
def agenda_comercial():
    """Consolida apenas atividades operacionais ligadas ao núcleo comercial ativo."""
    oportunidades = {item.get("id"): item for item in _oportunidades_comerciais()}
    atividades = [item for item in _lista("cti_atividades") if _registro_operacional(item)]

    itens = []
    for atividade in atividades:
        oportunidade = oportunidades.get(atividade.get("oportunidade_id"), {})
        if atividade.get("oportunidade_id") and not oportunidade:
            continue
        itens.append({
            **atividade,
            "situacao": _situacao_atividade(atividade),
            "oportunidade_titulo": _titulo_oportunidade(oportunidade) if oportunidade else None,
            "cliente_id": atividade.get("cliente_id") or oportunidade.get("cliente_id"),
            "responsavel_id": atividade.get("usuario_id") or oportunidade.get("responsavel_id"),
            "origem_oportunidade": oportunidade.get("origem"),
        })

    ordem_situacao = {"ATRASADA": 0, "HOJE": 1, "FUTURA": 2, "SEM_DATA": 3, "CONCLUIDA": 4, "CANCELADA": 5}
    itens.sort(key=lambda item: (ordem_situacao.get(item["situacao"], 9), item.get("data") or "9999-12-31", item.get("horario") or "23:59"))
    contagem = Counter(item["situacao"] for item in itens)

    return {
        "itens": itens,
        "resumo": {
            "total": len(itens),
            "atrasadas": contagem.get("ATRASADA", 0),
            "hoje": contagem.get("HOJE", 0),
            "futuras": contagem.get("FUTURA", 0),
            "sem_data": contagem.get("SEM_DATA", 0),
            "concluidas": contagem.get("CONCLUIDA", 0),
        },
    }


@router.get("/crm/timeline/{oportunidade_id}")
def timeline_oportunidade(oportunidade_id: str):
    """Monta a timeline usando somente fontes existentes e vínculos reais do schema."""
    try:
        oportunidade = (
            supabase.table("cti_oportunidades")
            .select("*")
            .eq("id", oportunidade_id)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao consultar a oportunidade: {exc}",
        ) from exc

    if not oportunidade:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")

    oportunidade_atual = oportunidade[0]
    oportunidade_enriquecida = {
        **oportunidade_atual,
        "titulo": _titulo_oportunidade(oportunidade_atual),
        "cliente_nome": _nome_cliente(oportunidade_atual.get("cliente_id")),
    }
    eventos: list[dict[str, Any]] = [{
        "tipo": "OPORTUNIDADE",
        "data_hora": oportunidade_atual.get("created_at") or oportunidade_atual.get("updated_at"),
        "titulo": _titulo_oportunidade(oportunidade_atual),
        "status": oportunidade_atual.get("status") or "OPORTUNIDADE",
        "responsavel_id": oportunidade_atual.get("responsavel_id"),
        "registro": oportunidade_enriquecida,
    }]
    fontes_indisponiveis: list[str] = []

    registros_por_tipo: dict[str, list[dict[str, Any]]] = {}
    for tipo, tabela in (
        ("ATIVIDADE", "cti_atividades"),
        ("PIPELINE", "cti_pipeline"),
        ("PROPOSTA", "cti_propostas"),
    ):
        try:
            registros_por_tipo[tipo] = _consultar_oportunidade(tabela, oportunidade_id)
        except Exception:
            registros_por_tipo[tipo] = []
            fontes_indisponiveis.append(tabela)

    try:
        itens = _consultar_oportunidade("cti_oportunidade_itens", oportunidade_id)
    except Exception:
        itens = []
        fontes_indisponiveis.append("cti_oportunidade_itens")

    try:
        registros_por_tipo["PEDIDO"] = _pedidos_da_oportunidade(registros_por_tipo.get("PROPOSTA", []), itens)
    except Exception:
        registros_por_tipo["PEDIDO"] = []
        fontes_indisponiveis.append("cti_pedidos")

    for tipo in ("ATIVIDADE", "PIPELINE", "PROPOSTA", "PEDIDO"):
        for registro in registros_por_tipo.get(tipo, []):
            eventos.append(_evento(tipo, registro))

    eventos.sort(key=lambda item: str(item.get("data_hora") or ""), reverse=True)
    return {
        "oportunidade": oportunidade_enriquecida,
        "eventos": eventos,
        "fontes_indisponiveis": sorted(set(fontes_indisponiveis)),
        "parcial": bool(fontes_indisponiveis),
    }
