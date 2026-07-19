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
    "OPORTUNIDADE",
    "ATIVIDADES",
    "PROPOSTA",
    "NEGOCIACAO",
    "PEDIDO",
    "CONCLUSAO",
    "INTELIGENCIA",
    "GANHO",
    "PERDIDO",
]

ETAPAS_ABERTAS = {
    "OPORTUNIDADE",
    "ATIVIDADES",
    "PROPOSTA",
    "NEGOCIACAO",
    "PEDIDO",
    "PROSPECCAO",
    "QUALIFICACAO",
    "VISITA",
    "FECHAMENTO",
}

STATUS_PROPOSTA = [
    "ELABORACAO",
    "ENVIADA",
    "EM_ANALISE",
    "NEGOCIACAO",
    "APROVADA",
    "REJEITADA",
    "EXPIRADA",
    "CANCELADA",
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
    linha_equipamentos: Optional[str] = None
    equipamento: Optional[str] = None
    implementadora: Optional[str] = None
    locadora: Optional[str] = None
    estado: Optional[str] = None
    ddd: Optional[str] = None
    sub_regiao: Optional[str] = None
    municipio: Optional[str] = None
    bairro: Optional[str] = None
    observacoes: Optional[str] = None
    status: str = "OPORTUNIDADE"


class OportunidadeUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    origem: Optional[str] = None
    status: Optional[str] = None
    valor_estimado: Optional[float] = None
    probabilidade: Optional[float] = None
    data_fechamento_prevista: Optional[str] = None
    contato_id: Optional[str] = None
    linha_equipamentos: Optional[str] = None
    equipamento: Optional[str] = None
    implementadora: Optional[str] = None
    locadora: Optional[str] = None
    estado: Optional[str] = None
    ddd: Optional[str] = None
    sub_regiao: Optional[str] = None
    municipio: Optional[str] = None
    bairro: Optional[str] = None
    observacoes: Optional[str] = None


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
    status: str = "ELABORACAO"
    responsavel_id: Optional[str] = None
    validade: Optional[str] = None
    observacoes: Optional[str] = None
    produtos: Optional[str] = None
    equipamentos: Optional[str] = None
    condicoes: Optional[str] = None


class PropostaUpdate(BaseModel):
    numero: Optional[str] = None
    cliente_id: Optional[str] = None
    oportunidade_id: Optional[str] = None
    valor: Optional[float] = None
    status: Optional[str] = None
    responsavel_id: Optional[str] = None
    validade: Optional[str] = None
    observacoes: Optional[str] = None
    produtos: Optional[str] = None
    equipamentos: Optional[str] = None
    condicoes: Optional[str] = None


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


class PerdaCreate(BaseModel):
    motivo: str
    concorrente: Optional[str] = None
    responsavel_id: str
    valor_perdido: float = 0
    observacoes: Optional[str] = None
    data: Optional[str] = None


class ConverterPedidoCreate(BaseModel):
    numero: str
    responsavel_id: Optional[str] = None
    data_pedido: Optional[str] = None
    origem_comercial: Optional[str] = "CRM"
    status: str = "ABERTO"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_hour() -> tuple[str, str]:
    agora = datetime.now(timezone.utc)
    return agora.date().isoformat(), agora.time().replace(microsecond=0).isoformat()


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
    return {field: getattr(model, field) for field in fields if hasattr(model, field) and getattr(model, field) is not None}


def _normalizar_probabilidade(probability: Any) -> float:
    try:
        value = float(probability or 0)
    except (TypeError, ValueError):
        return 0
    if value < 0:
        return 0
    if value <= 1:
        return value
    return value / 100


def _probability_factor(probability: Any) -> float:
    return _normalizar_probabilidade(probability)


def _registrar_historico(oportunidade_id: str, tipo: str, descricao: str, usuario_id: Optional[str] = None, payload: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    registro = {
        "oportunidade_id": oportunidade_id,
        "tipo": tipo,
        "descricao": descricao,
        "usuario_id": usuario_id,
        "payload": payload or {},
        "created_at": _now(),
    }
    return _insert("cti_oportunidade_historico", registro)


def _registrar_auditoria(entidade: str, entidade_id: str, acao: str, usuario_id: Optional[str] = None, payload: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    return _insert("cti_crm_auditoria", {
        "entidade": entidade,
        "entidade_id": entidade_id,
        "acao": acao,
        "usuario_id": usuario_id,
        "payload": payload or {},
        "created_at": _now(),
    })


def _registrar_pipeline(oportunidade_id: str, etapa_anterior: Optional[str], nova_etapa: str, usuario_id: Optional[str], observacao: Optional[str] = None) -> list[dict[str, Any]]:
    data, hora = _date_hour()
    payload = {
        "oportunidade_id": oportunidade_id,
        "etapa_anterior": etapa_anterior,
        "nova_etapa": nova_etapa,
        "etapa": nova_etapa,
        "usuario_id": usuario_id,
        "observacao": observacao,
        "data": data,
        "hora": hora,
    }
    return _insert("cti_pipeline", payload)


def _campos_oportunidade() -> list[str]:
    return [
        "cliente_id", "responsavel_id", "titulo", "descricao", "origem", "status",
        "valor_estimado", "probabilidade", "data_fechamento_prevista", "contato_id",
        "linha_equipamentos", "equipamento", "implementadora", "locadora", "estado",
        "ddd", "sub_regiao", "municipio", "bairro", "observacoes",
    ]


def _campos_proposta() -> list[str]:
    return [
        "numero", "cliente_id", "oportunidade_id", "valor", "status", "responsavel_id",
        "validade", "observacoes", "produtos", "equipamentos", "condicoes",
    ]


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
    payload = _payload(oportunidade, _campos_oportunidade())
    payload["probabilidade"] = _normalizar_probabilidade(payload.get("probabilidade"))
    created = _insert("cti_oportunidades", payload)
    oportunidade_criada = created[0]
    oportunidade_id = oportunidade_criada["id"]
    _registrar_pipeline(oportunidade_id, None, payload.get("status") or "OPORTUNIDADE", payload.get("responsavel_id"), "Primeira movimentação automática da oportunidade.")
    _registrar_historico(oportunidade_id, "OPORTUNIDADE", "Oportunidade criada e primeira movimentação registrada.", payload.get("responsavel_id"), oportunidade_criada)
    _registrar_auditoria("cti_oportunidades", oportunidade_id, "CRIACAO", payload.get("responsavel_id"), oportunidade_criada)
    return created


@router.put("/oportunidades/{oportunidade_id}")
def atualizar_oportunidade(oportunidade_id: str, oportunidade: OportunidadeUpdate):
    anterior = _first("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada")
    payload = _payload(oportunidade, _campos_oportunidade())
    if "probabilidade" in payload:
        payload["probabilidade"] = _normalizar_probabilidade(payload.get("probabilidade"))
    updated = _update("cti_oportunidades", oportunidade_id, payload, "Oportunidade não encontrada")
    if payload.get("status") and payload.get("status") != anterior.get("status"):
        _registrar_pipeline(oportunidade_id, anterior.get("status"), payload["status"], payload.get("responsavel_id") or anterior.get("responsavel_id"), payload.get("observacoes"))
    _registrar_historico(oportunidade_id, "OPORTUNIDADE", "Oportunidade atualizada.", payload.get("responsavel_id") or anterior.get("responsavel_id"), payload)
    _registrar_auditoria("cti_oportunidades", oportunidade_id, "ATUALIZACAO", payload.get("responsavel_id") or anterior.get("responsavel_id"), payload)
    return updated


@router.delete("/oportunidades/{oportunidade_id}")
def excluir_oportunidade(oportunidade_id: str):
    supabase.table("cti_oportunidades").delete().eq("id", oportunidade_id).execute()
    return {"success": True}


@router.post("/oportunidades/{oportunidade_id}/perdas")
def registrar_perda(oportunidade_id: str, perda: PerdaCreate):
    oportunidade = _first("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada")
    payload = _payload(perda, ["motivo", "concorrente", "responsavel_id", "valor_perdido", "observacoes", "data"])
    payload["oportunidade_id"] = oportunidade_id
    payload["data"] = payload.get("data") or datetime.now(timezone.utc).date().isoformat()
    created = _insert("cti_perdas", payload)
    _update("cti_oportunidades", oportunidade_id, {"status": "PERDIDO"}, "Oportunidade não encontrada")
    _registrar_pipeline(oportunidade_id, oportunidade.get("status"), "PERDIDO", perda.responsavel_id, perda.observacoes)
    _registrar_historico(oportunidade_id, "PERDA", "Perda registrada automaticamente no histórico.", perda.responsavel_id, created[0])
    _registrar_auditoria("cti_perdas", created[0]["id"], "CRIACAO", perda.responsavel_id, created[0])
    return created


@router.get("/pipeline")
def listar_pipeline():
    dados = supabase.table("cti_pipeline").select("*").order("created_at", desc=True).execute().data or []
    return sorted(dados, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)


@router.post("/pipeline")
def criar_pipeline(pipeline: PipelineCreate):
    oportunidade = _first("cti_oportunidades", pipeline.oportunidade_id, "Oportunidade não encontrada")
    created = _registrar_pipeline(pipeline.oportunidade_id, oportunidade.get("status"), pipeline.etapa, pipeline.usuario_id, pipeline.observacao)
    _update("cti_oportunidades", pipeline.oportunidade_id, {"status": pipeline.etapa}, "Oportunidade não encontrada")
    _registrar_historico(pipeline.oportunidade_id, "PIPELINE", "Movimentação de pipeline registrada.", pipeline.usuario_id, created[0])
    return created


@router.put("/pipeline/{pipeline_id}")
def atualizar_pipeline(pipeline_id: str, pipeline: PipelineUpdate):
    atual = _first("cti_pipeline", pipeline_id, "Pipeline não encontrado")
    payload = _payload(pipeline, ["etapa", "observacao"])
    if pipeline.etapa is not None:
        payload["nova_etapa"] = pipeline.etapa
    updated = _update("cti_pipeline", pipeline_id, payload, "Pipeline não encontrado")
    if pipeline.etapa is not None and updated:
        oportunidade_id = updated[0].get("oportunidade_id")
        if oportunidade_id:
            oportunidade = _first("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada")
            _update("cti_oportunidades", oportunidade_id, {"status": pipeline.etapa}, "Oportunidade não encontrada")
            _registrar_historico(oportunidade_id, "PIPELINE", "Movimentação de pipeline atualizada.", atual.get("usuario_id"), {"etapa_anterior": oportunidade.get("status"), "nova_etapa": pipeline.etapa})
    return updated


@router.get("/propostas")
def listar_propostas():
    return supabase.table("cti_propostas").select("*").order("created_at", desc=True).execute().data


@router.get("/propostas/{proposta_id}")
def obter_proposta(proposta_id: str):
    return _first("cti_propostas", proposta_id, "Proposta não encontrada")


@router.post("/propostas")
def criar_proposta(proposta: PropostaCreate):
    _first("cti_oportunidades", proposta.oportunidade_id, "Oportunidade não encontrada")
    payload = _payload(proposta, _campos_proposta())
    created = _insert("cti_propostas", payload)
    _update("cti_oportunidades", proposta.oportunidade_id, {"status": "PROPOSTA"}, "Oportunidade não encontrada")
    _registrar_pipeline(proposta.oportunidade_id, None, "PROPOSTA", proposta.responsavel_id, "Proposta criada a partir da oportunidade.")
    _registrar_historico(proposta.oportunidade_id, "PROPOSTA", "Proposta criada exclusivamente a partir da oportunidade.", proposta.responsavel_id, created[0])
    return created


@router.put("/propostas/{proposta_id}")
def atualizar_proposta(proposta_id: str, proposta: PropostaUpdate):
    updated = _update("cti_propostas", proposta_id, _payload(proposta, _campos_proposta()), "Proposta não encontrada")
    if updated and updated[0].get("oportunidade_id"):
        _registrar_historico(updated[0]["oportunidade_id"], "PROPOSTA", "Proposta atualizada.", updated[0].get("responsavel_id"), updated[0])
    return updated


@router.post("/propostas/{proposta_id}/converter-pedido")
def converter_proposta_em_pedido(proposta_id: str, conversao: ConverterPedidoCreate):
    proposta = _first("cti_propostas", proposta_id, "Proposta não encontrada")
    oportunidade_id = proposta.get("oportunidade_id")
    if not oportunidade_id:
        raise HTTPException(status_code=400, detail="Proposta sem oportunidade vinculada")
    oportunidade = _first("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada")
    pedido_payload = {
        "numero": conversao.numero,
        "cliente_id": proposta.get("cliente_id"),
        "proposta_id": proposta_id,
        "oportunidade_id": oportunidade_id,
        "responsavel_id": conversao.responsavel_id or proposta.get("responsavel_id") or oportunidade.get("responsavel_id"),
        "valor": proposta.get("valor") or oportunidade.get("valor_estimado") or 0,
        "status": conversao.status,
        "data_pedido": conversao.data_pedido or datetime.now(timezone.utc).date().isoformat(),
        "origem_comercial": conversao.origem_comercial,
    }
    pedido = _insert("cti_pedidos", pedido_payload)
    _update("cti_propostas", proposta_id, {"status": "APROVADA"}, "Proposta não encontrada")
    _update("cti_oportunidades", oportunidade_id, {"status": "GANHO"}, "Oportunidade não encontrada")
    _registrar_pipeline(oportunidade_id, oportunidade.get("status"), "GANHO", pedido_payload.get("responsavel_id"), "Proposta convertida em pedido.")
    _registrar_historico(oportunidade_id, "PEDIDO", "Proposta aprovada e convertida em pedido.", pedido_payload.get("responsavel_id"), pedido[0])
    _registrar_auditoria("cti_pedidos", pedido[0]["id"], "CONVERSAO_PROPOSTA_PEDIDO", pedido_payload.get("responsavel_id"), pedido[0])
    return pedido


@router.get("/pedidos")
def listar_pedidos():
    return supabase.table("cti_pedidos").select("*").order("created_at", desc=True).execute().data


@router.get("/pedidos/{pedido_id}")
def obter_pedido(pedido_id: str):
    return _first("cti_pedidos", pedido_id, "Pedido não encontrado")


@router.post("/pedidos")
def criar_pedido(pedido: PedidoCreate):
    created = _insert("cti_pedidos", _payload(pedido, ["numero", "cliente_id", "proposta_id", "oportunidade_id", "responsavel_id", "valor", "status", "data_pedido", "origem_comercial"]))
    if pedido.oportunidade_id:
        _registrar_historico(pedido.oportunidade_id, "PEDIDO", "Pedido criado e vinculado à oportunidade.", pedido.responsavel_id, created[0])
    return created


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
    payload = _payload(atividade, ["cliente_id", "oportunidade_id", "proposta_id", "pedido_id", "usuario_id", "tipo", "titulo", "descricao", "data", "horario", "status"])
    created = _insert("cti_atividades", payload)
    if atividade.oportunidade_id:
        _registrar_historico(atividade.oportunidade_id, "ATIVIDADE", "Atividade registrada na oportunidade.", atividade.usuario_id, created[0])
    return created


@router.put("/atividades/{atividade_id}")
def atualizar_atividade(atividade_id: str, atividade: AtividadeUpdate):
    updated = _update("cti_atividades", atividade_id, _payload(atividade, ["cliente_id", "oportunidade_id", "proposta_id", "pedido_id", "usuario_id", "tipo", "titulo", "descricao", "data", "horario", "status"]), "Atividade não encontrada")
    if updated and updated[0].get("oportunidade_id"):
        _registrar_historico(updated[0]["oportunidade_id"], "ATIVIDADE", "Atividade atualizada na oportunidade.", updated[0].get("usuario_id"), updated[0])
    return updated


@router.put("/atividades/{atividade_id}/concluir")
def concluir_atividade(atividade_id: str):
    updated = _update("cti_atividades", atividade_id, {"status": "CONCLUIDA", "concluida_em": _now()}, "Atividade não encontrada")
    if updated and updated[0].get("oportunidade_id"):
        _registrar_historico(updated[0]["oportunidade_id"], "ATIVIDADE", "Atividade concluída.", updated[0].get("usuario_id"), updated[0])
    return updated


@router.get("/dashboard")
def dashboard_crm():
    return {
        "oportunidades": len(listar_oportunidades()),
        "propostas": len(listar_propostas()),
        "pedidos": len(listar_pedidos()),
        "atividades": len(listar_atividades()),
        "contexto": {
            "origem": "CRM operacional",
            "periodo": "Oportunidades cadastradas no módulo CRM",
            "significado": "Indicadores de operações futuras, sem uso da base histórica de vendas.",
            "criterio_calculo": "Contagem dos registros operacionais próprios do CRM por tabela.",
            "finalidade_operacional": "Acompanhar criação, avanço e conversão de oportunidades comerciais.",
        },
    }


@router.get("/resumo")
def resumo_comercial():
    oportunidades = listar_oportunidades()
    abertas = [item for item in oportunidades if (item.get("status") or "OPORTUNIDADE") in ETAPAS_ABERTAS]
    return {"qtd_oportunidades": len(abertas), "valor_pipeline": sum(float(item.get("valor_estimado", 0) or 0) for item in abertas)}


@router.get("/forecast")
def forecast_comercial():
    oportunidades = [item for item in listar_oportunidades() if (item.get("status") or "OPORTUNIDADE") in ETAPAS_ABERTAS]
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
        {"id": f"{etapa}:{responsavel}:{periodo}", "fase": etapa, "vendedor": responsavel, "carteira": periodo, "status": etapa, "pipeline_total": round(valores["pipeline_total"], 2), "pipeline_ponderado": round(valores["pipeline_ponderado"], 2), "meta": 0, "qtd_oportunidades": valores["qtd_oportunidades"], "contexto": {"origem": "CRM operacional", "periodo": periodo, "criterio_calculo": "Somente oportunidades abertas; pedidos concluídos e vendas históricas excluídos.", "finalidade_operacional": "Projetar carteira comercial futura."}}
        for (etapa, responsavel, periodo), valores in sorted(grupos.items())
    ]


@router.get("/status")
def status_crm():
    return {"modulo": "CRM", "fase": "16.2", "status": "OPERACIONAL"}
