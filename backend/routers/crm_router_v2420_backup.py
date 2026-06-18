# ============================================================
# CTI CRM ROUTER
# FASE 2.4.2
# CRM Backend
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


class PipelineCreate(BaseModel):

    oportunidade_id: str

    etapa: str

    usuario_id: str

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
def obter_oportunidade(oportunidade_id: str):

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

    resultado = (
        supabase
        .table("cti_pipeline")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return resultado.data


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
# STATUS
# ============================================================

@router.get("/status")
def status_crm():

    return {
        "modulo": "CRM",
        "fase": "2.4.2",
        "status": "OPERACIONAL"
    }