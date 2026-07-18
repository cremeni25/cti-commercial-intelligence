from collections import defaultdict
from datetime import datetime, timezone
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

router = APIRouter(prefix="/crm", tags=["CRM"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase não configurado")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ETAPAS_CRM = [
    "PROSPECCAO",
    "QUALIFICACAO",
    "VISITA",
    "PROPOSTA",
    "NEGOCIACAO",
    "FECHAMENTO",
    "GANHO",
    "PERDIDO",
]


class OportunidadeCreate(BaseModel):
    cliente_id: str
    responsavel_id: str
    titulo: str
    descricao: Optional[str] = None
    origem: Optional[str] = None
    valor_estimado: float = 0
    probabilidade: float = 0
    data_fechamento_prevista: Optional[str] = None
    contato_id: Optional[str] = None
    status: str = "PROSPECCAO"


class OportunidadeUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    origem: Optional[str] = None
    status: Optional[str] = None
    valor_estimado: Optional[float] = None
    probabilidade: Optional[float] = None
    data_fechamento_prevista: Optional[str] = None
    contato_id: Optional[str] = None


class PipelineCreate(BaseModel):
    oportunidade_id: str
    etapa: str
    usuario_id: str
    observacao: Optional[str] = None


class PipelineUpdate(BaseModel):
    etapa: Optional[str] = None
    observacao: Optional[str] = None


class PropostaCreate(BaseModel):
    numero: str
    cliente_id: str
    oportunidade_id: str
    valor: float
    status: str = "EM_ABERTO"
    responsavel_id: Optional[str] = None
    validade: Optional[str] = None
    observacoes: Optional[str] = None


class PropostaUpdate(BaseModel):
    numero: Optional[str] = None
    cliente_id: Optional[str] = None
    oportunidade_id: Optional[str] = None
    valor: Optional[float] = None
    status: Optional[str] = None
    responsavel_id: Optional[str] = None
    validade: Optional[str] = None
    observacoes: Optional[str] = None


class PedidoCreate(BaseModel):
    numero: str
    cliente_id: str
    proposta_id: str
    valor: float
    status: str = "ABERTO"
    oportunidade_id: Optional[str] = None
    responsavel_id: Optional[str] = None
    data_pedido: Optional[str] = None
    origem_comercial: Optional[str] = None


class PedidoUpdate(BaseModel):
    numero: Optional[str] = None
    cliente_id: Optional[str] = None
    proposta_id: Optional[str] = None
    oportunidade_id: Optional[str] = None
    responsavel_id: Optional[str] = None
    valor: Optional[float] = None
    status: Optional[str] = None
    data_pedido: Optional[str] = None
    origem_comercial: Optional[str] = None


class AtividadeCreate(BaseModel):
    cliente_id: str
    oportunidade_id: Optional[str] = None
    proposta_id: Optional[str] = None
    pedido_id: Optional[str] = None
    usuario_id: str
    tipo: str
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data: Optional[str] = None
    horario: Optional[str] = None
    status: str = "PENDENTE"


class AtividadeUpdate(BaseModel):
    cliente_id: Optional[str] = None
    oportunidade_id: Optional[str] = None
    proposta_id: Optional[str] = None
    pedido_id: Optional[str] = None
    usuario_id: Optional[str] = None
    tipo: Optional[str] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data: Optional[str] = None
    horario: Optional[str] = None
    status: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _first(table: str, record_id: str, detail: str) -> dict[str, Any]:
    result = supabase.table(table).select("*").eq("id", record_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=detail)
    return result.data[0]


def _insert(table: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    return supabase.table(table).insert(payload).execute().data


def _update(table: str, record_id: str, payload: dict[str, Any], detail: str) -> list[dict[str, Any]]:
    if not payload:
        return [_first(table, record_id, detail)]
    payload["updated_at"] = _now()
    result = supabase.table(table).update(payload).eq("id", record_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=detail)
    return result.data


def _payload(model: BaseModel, fields: list[str]) -> dict[str, Any]:
    return {field: getattr(model, field) for field in fields if getattr(model, field) is not None}


def _probability_factor(probability: Any) -> float:
    try:
        value = float(probability or 0)
    except (TypeError, ValueError):
        return 0
    if value < 0:
        return 0
    if value <= 1:
        return value
    return value / 100


@router.get("/etapas")
def listar_etapas():
    return ETAPAS_CRM


@router.get("/oportunidades")
def listar_oportunidades():
    return supabase.table("cti_oportunidades").select("*").order("created_at", desc=True).execute().data


@router.get("/oportunidades/{oportunidade_id}")
def obter_oportunidade(oportunidade_id: str):
    return _first("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada")


@router.post("/oportunidades")
def criar_oportunidade(oportunidade: OportunidadeCreate):
    payload = _payload(oportunidade, [
        "cliente_id", "responsavel_id", "titulo", "descricao", "origem", "status",
        "valor_estimado", "probabilidade", "data_fechamento_prevista", "contato_id",
    ])
    return _insert("cti_oportunidades", payload)


@router.put("/oportunidades/{oportunidade_id}")
def atualizar_oportunidade(oportunidade_id: str, oportunidade: OportunidadeUpdate):
    payload = _payload(oportunidade, [
        "titulo", "descricao", "origem", "status", "valor_estimado", "probabilidade",
        "data_fechamento_prevista", "contato_id",
    ])
    return _update("cti_oportunidades", oportunidade_id, payload, "Oportunidade não encontrada")


@router.delete("/oportunidades/{oportunidade_id}")
def excluir_oportunidade(oportunidade_id: str):
    supabase.table("cti_oportunidades").delete().eq("id", oportunidade_id).execute()
    return {"success": True}


@router.get("/pipeline")
def listar_pipeline():
    oportunidades = listar_oportunidades()
    return [dict(item, etapa=item.get("status") or item.get("etapa") or "PROSPECCAO", oportunidade_id=item.get("id")) for item in oportunidades]


@router.post("/pipeline")
def criar_pipeline(pipeline: PipelineCreate):
    payload = _payload(pipeline, ["oportunidade_id", "etapa", "usuario_id", "observacao"])
    created = _insert("cti_pipeline", payload)
    _update("cti_oportunidades", pipeline.oportunidade_id, {"status": pipeline.etapa}, "Oportunidade não encontrada")
    return created


@router.put("/pipeline/{pipeline_id}")
def atualizar_pipeline(pipeline_id: str, pipeline: PipelineUpdate):
    payload = _payload(pipeline, ["etapa", "observacao"])
    updated = _update("cti_pipeline", pipeline_id, payload, "Pipeline não encontrado")
    if pipeline.etapa is not None and updated:
        oportunidade_id = updated[0].get("oportunidade_id")
        if oportunidade_id:
            _update("cti_oportunidades", oportunidade_id, {"status": pipeline.etapa}, "Oportunidade não encontrada")
    return updated


@router.get("/propostas")
def listar_propostas():
    return supabase.table("cti_propostas").select("*").order("created_at", desc=True).execute().data


@router.get("/propostas/{proposta_id}")
def obter_proposta(proposta_id: str):
    return _first("cti_propostas", proposta_id, "Proposta não encontrada")


@router.post("/propostas")
def criar_proposta(proposta: PropostaCreate):
    return _insert("cti_propostas", _payload(proposta, ["numero", "cliente_id", "oportunidade_id", "valor", "status", "responsavel_id", "validade", "observacoes"]))


@router.put("/propostas/{proposta_id}")
def atualizar_proposta(proposta_id: str, proposta: PropostaUpdate):
    return _update("cti_propostas", proposta_id, _payload(proposta, ["numero", "cliente_id", "oportunidade_id", "valor", "status", "responsavel_id", "validade", "observacoes"]), "Proposta não encontrada")


@router.get("/pedidos")
def listar_pedidos():
    return supabase.table("cti_pedidos").select("*").order("created_at", desc=True).execute().data


@router.get("/pedidos/{pedido_id}")
def obter_pedido(pedido_id: str):
    return _first("cti_pedidos", pedido_id, "Pedido não encontrado")


@router.post("/pedidos")
def criar_pedido(pedido: PedidoCreate):
    return _insert("cti_pedidos", _payload(pedido, ["numero", "cliente_id", "proposta_id", "oportunidade_id", "responsavel_id", "valor", "status", "data_pedido", "origem_comercial"]))


@router.put("/pedidos/{pedido_id}")
def atualizar_pedido(pedido_id: str, pedido: PedidoUpdate):
    return _update("cti_pedidos", pedido_id, _payload(pedido, ["numero", "cliente_id", "proposta_id", "oportunidade_id", "responsavel_id", "valor", "status", "data_pedido", "origem_comercial"]), "Pedido não encontrado")


@router.get("/atividades")
def listar_atividades():
    return supabase.table("cti_atividades").select("*").order("created_at", desc=True).execute().data


@router.get("/atividades/{atividade_id}")
def obter_atividade(atividade_id: str):
    return _first("cti_atividades", atividade_id, "Atividade não encontrada")


@router.post("/atividades")
def criar_atividade(atividade: AtividadeCreate):
    return _insert("cti_atividades", _payload(atividade, ["cliente_id", "oportunidade_id", "proposta_id", "pedido_id", "usuario_id", "tipo", "titulo", "descricao", "data", "horario", "status"]))


@router.put("/atividades/{atividade_id}")
def atualizar_atividade(atividade_id: str, atividade: AtividadeUpdate):
    return _update("cti_atividades", atividade_id, _payload(atividade, ["cliente_id", "oportunidade_id", "proposta_id", "pedido_id", "usuario_id", "tipo", "titulo", "descricao", "data", "horario", "status"]), "Atividade não encontrada")


@router.put("/atividades/{atividade_id}/concluir")
def concluir_atividade(atividade_id: str):
    return _update("cti_atividades", atividade_id, {"status": "CONCLUIDA", "concluida_em": _now()}, "Atividade não encontrada")


@router.get("/dashboard")
def dashboard_crm():
    return {"oportunidades": len(listar_oportunidades()), "propostas": len(listar_propostas()), "pedidos": len(listar_pedidos()), "atividades": len(listar_atividades())}


@router.get("/resumo")
def resumo_comercial():
    oportunidades = listar_oportunidades()
    return {"qtd_oportunidades": len(oportunidades), "valor_pipeline": sum(float(item.get("valor_estimado", 0) or 0) for item in oportunidades)}


@router.get("/forecast")
def forecast_comercial():
    oportunidades = listar_oportunidades()
    grupos: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(lambda: {"pipeline_total": 0.0, "pipeline_ponderado": 0.0, "qtd_oportunidades": 0})
    for item in oportunidades:
        try:
            valor = float(item.get("valor_estimado", 0) or 0)
        except (TypeError, ValueError):
            continue
        etapa = item.get("status") or item.get("etapa") or "SEM_STATUS"
        responsavel = item.get("responsavel_id") or "SEM_RESPONSAVEL"
        periodo = (item.get("data_fechamento_prevista") or item.get("created_at") or "SEM_PERIODO")[:7]
        key = (etapa, responsavel, periodo)
        grupos[key]["pipeline_total"] += valor
        grupos[key]["pipeline_ponderado"] += valor * _probability_factor(item.get("probabilidade"))
        grupos[key]["qtd_oportunidades"] += 1
    return [
        {"id": f"{etapa}:{responsavel}:{periodo}", "fase": etapa, "vendedor": responsavel, "carteira": periodo, "status": etapa, "pipeline_total": round(valores["pipeline_total"], 2), "pipeline_ponderado": round(valores["pipeline_ponderado"], 2), "meta": 0, "qtd_oportunidades": valores["qtd_oportunidades"]}
        for (etapa, responsavel, periodo), valores in sorted(grupos.items())
    ]


@router.get("/status")
def status_crm():
    return {"modulo": "CRM", "fase": "16.1", "status": "OPERACIONAL"}
