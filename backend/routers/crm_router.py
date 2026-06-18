# ============================================================
# CTI CRM ROUTER
# VERSÃO 2.4.2.1 CONSOLIDADA
# PARTE 1/2
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client
import os

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/crm",
    tags=["CRM"]
)

# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase não configurado")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ============================================================
# ETAPAS OFICIAIS CTI
# ============================================================

ETAPAS_CRM = [

    "PROSPECCAO",
    "QUALIFICACAO",
    "VISITA",
    "PROPOSTA",
    "NEGOCIACAO",
    "FECHAMENTO",
    "GANHO",
    "PERDIDO"
]

# ============================================================
# MODELS
# ============================================================

class OportunidadeCreate(BaseModel):

    cliente_id: str
    responsavel_id: str

    titulo: str

    descricao: Optional[str] = None

    origem: Optional[str] = None

    valor_estimado: float = 0

    probabilidade: int = 0


class OportunidadeUpdate(BaseModel):

    titulo: Optional[str] = None

    descricao: Optional[str] = None

    origem: Optional[str] = None

    status: Optional[str] = None

    valor_estimado: Optional[float] = None

    probabilidade: Optional[int] = None


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


class PedidoCreate(BaseModel):

    numero: str

    cliente_id: str

    proposta_id: str

    valor: float

    status: str = "ABERTO"


class AtividadeCreate(BaseModel):

    cliente_id: str

    oportunidade_id: str

    usuario_id: str

    tipo: str

    descricao: Optional[str] = None

    status: str = "PENDENTE"

# ============================================================
# ETAPAS CRM
# ============================================================

@router.get("/etapas")
def listar_etapas():

    return ETAPAS_CRM

# ============================================================
# OPORTUNIDADES
# ============================================================

@router.get("/oportunidades")
def listar_oportunidades():

    resultado = (
        supabase
        .table("cti_oportunidades")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return resultado.data


@router.get("/oportunidades/{oportunidade_id}")
def obter_oportunidade(
    oportunidade_id: str
):

    resultado = (
        supabase
        .table("cti_oportunidades")
        .select("*")
        .eq("id", oportunidade_id)
        .execute()
    )

    if not resultado.data:

        raise HTTPException(
            status_code=404,
            detail="Oportunidade não encontrada"
        )

    return resultado.data[0]


@router.post("/oportunidades")
def criar_oportunidade(
    oportunidade: OportunidadeCreate
):

    payload = {

        "cliente_id":
            oportunidade.cliente_id,

        "responsavel_id":
            oportunidade.responsavel_id,

        "titulo":
            oportunidade.titulo,

        "descricao":
            oportunidade.descricao,

        "origem":
            oportunidade.origem,

        "status":
            "PROSPECCAO",

        "valor_estimado":
            oportunidade.valor_estimado,

        "probabilidade":
            oportunidade.probabilidade
    }

    resultado = (
        supabase
        .table("cti_oportunidades")
        .insert(payload)
        .execute()
    )

    return resultado.data


@router.put("/oportunidades/{oportunidade_id}")
def atualizar_oportunidade(
    oportunidade_id: str,
    oportunidade: OportunidadeUpdate
):

    payload = {}

    if oportunidade.titulo is not None:
        payload["titulo"] = oportunidade.titulo

    if oportunidade.descricao is not None:
        payload["descricao"] = oportunidade.descricao

    if oportunidade.origem is not None:
        payload["origem"] = oportunidade.origem

    if oportunidade.status is not None:
        payload["status"] = oportunidade.status

    if oportunidade.valor_estimado is not None:
        payload["valor_estimado"] = oportunidade.valor_estimado

    if oportunidade.probabilidade is not None:
        payload["probabilidade"] = oportunidade.probabilidade

    resultado = (
        supabase
        .table("cti_oportunidades")
        .update(payload)
        .eq("id", oportunidade_id)
        .execute()
    )

    return resultado.data


@router.delete("/oportunidades/{oportunidade_id}")
def excluir_oportunidade(
    oportunidade_id: str
):

    (
        supabase
        .table("cti_oportunidades")
        .delete()
        .eq("id", oportunidade_id)
        .execute()
    )

    return {
        "success": True
    }

# ============================================================
# PIPELINE
# ============================================================

@router.get("/pipeline")
def listar_pipeline():

    try:

        resultado = (
            supabase
            .table("cti_pipeline")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return resultado.data

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/pipeline")
def criar_pipeline(
    pipeline: PipelineCreate
):

    resultado = (
        supabase
        .table("cti_pipeline")
        .insert({

            "oportunidade_id":
                pipeline.oportunidade_id,

            "etapa":
                pipeline.etapa,

            "usuario_id":
                pipeline.usuario_id,

            "observacao":
                pipeline.observacao
        })
        .execute()
    )

    return resultado.data


@router.put("/pipeline/{pipeline_id}")
def atualizar_pipeline(
    pipeline_id: str,
    pipeline: PipelineUpdate
):

    payload = {}

    if pipeline.etapa is not None:
        payload["etapa"] = pipeline.etapa

    if pipeline.observacao is not None:
        payload["observacao"] = pipeline.observacao

    resultado = (
        supabase
        .table("cti_pipeline")
        .update(payload)
        .eq("id", pipeline_id)
        .execute()
    )

    return resultado.data

# ============================================================
# PROPOSTAS
# ============================================================

@router.get("/propostas")
def listar_propostas():

    resultado = (
        supabase
        .table("cti_propostas")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return resultado.data


@router.post("/propostas")
def criar_proposta(
    proposta: PropostaCreate
):

    resultado = (
        supabase
        .table("cti_propostas")
        .insert({

            "numero":
                proposta.numero,

            "cliente_id":
                proposta.cliente_id,

            "oportunidade_id":
                proposta.oportunidade_id,

            "valor":
                proposta.valor,

            "status":
                proposta.status
        })
        .execute()
    )

    return resultado.data


# ============================================================
# PEDIDOS
# ============================================================

@router.get("/pedidos")
def listar_pedidos():

    resultado = (
        supabase
        .table("cti_pedidos")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return resultado.data


@router.post("/pedidos")
def criar_pedido(
    pedido: PedidoCreate
):

    resultado = (
        supabase
        .table("cti_pedidos")
        .insert({

            "numero":
                pedido.numero,

            "cliente_id":
                pedido.cliente_id,

            "proposta_id":
                pedido.proposta_id,

            "valor":
                pedido.valor,

            "status":
                pedido.status
        })
        .execute()
    )

    return resultado.data


# ============================================================
# ATIVIDADES
# ============================================================

@router.get("/atividades")
def listar_atividades():

    resultado = (
        supabase
        .table("cti_atividades")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return resultado.data


@router.post("/atividades")
def criar_atividade(
    atividade: AtividadeCreate
):

    resultado = (
        supabase
        .table("cti_atividades")
        .insert({

            "cliente_id":
                atividade.cliente_id,

            "oportunidade_id":
                atividade.oportunidade_id,

            "usuario_id":
                atividade.usuario_id,

            "tipo":
                atividade.tipo,

            "descricao":
                atividade.descricao,

            "status":
                atividade.status
        })
        .execute()
    )

    return resultado.data


# ============================================================
# DASHBOARD CRM
# ============================================================

@router.get("/dashboard")
def dashboard_crm():

    oportunidades = (
        supabase
        .table("cti_oportunidades")
        .select("*")
        .execute()
    )

    propostas = (
        supabase
        .table("cti_propostas")
        .select("*")
        .execute()
    )

    pedidos = (
        supabase
        .table("cti_pedidos")
        .select("*")
        .execute()
    )

    atividades = (
        supabase
        .table("cti_atividades")
        .select("*")
        .execute()
    )

    return {

        "oportunidades":
            len(oportunidades.data),

        "propostas":
            len(propostas.data),

        "pedidos":
            len(pedidos.data),

        "atividades":
            len(atividades.data)
    }


# ============================================================
# RESUMO COMERCIAL
# ============================================================

@router.get("/resumo")
def resumo_comercial():

    oportunidades = (
        supabase
        .table("cti_oportunidades")
        .select("valor_estimado")
        .execute()
    )

    valor_total = 0

    for item in oportunidades.data:

        valor_total += (
            item.get(
                "valor_estimado",
                0
            ) or 0
        )

    return {

        "qtd_oportunidades":
            len(oportunidades.data),

        "valor_pipeline":
            valor_total
    }

# ============================================================
# FORECAST COMERCIAL
# ============================================================

@router.get("/forecast")
def forecast_comercial():

    oportunidades = (
        supabase
        .table("cti_oportunidades")
        .select("*")
        .execute()
    )

    pipeline_total = 0
    pipeline_ponderado = 0

    for item in oportunidades.data:

        valor = float(
            item.get("valor_estimado", 0) or 0
        )

        probabilidade = float(
            item.get("probabilidade", 0) or 0
        )

        pipeline_total += valor

        pipeline_ponderado += (
            valor * (probabilidade / 100)
        )

    return [
        {
            "id": "CTI_GLOBAL",

            "vendedor":
                "CTI Comercial",

            "carteira":
                "Pipeline Corporativo",

            "pipeline_total":
                round(pipeline_total, 2),

            "pipeline_ponderado":
                round(pipeline_ponderado, 2),

            "meta":
                0
        }
    ]

# ============================================================
# STATUS CRM
# ============================================================

@router.get("/status")
def status_crm():

    return {

        "modulo":
            "CRM",

        "fase":
            "2.4.2.1",

        "status":
            "OPERACIONAL"
    }


