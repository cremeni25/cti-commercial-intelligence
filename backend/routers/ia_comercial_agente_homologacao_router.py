from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.ia_agente_homologacao_config import carregar_ia_agente_homologacao_config
from services.ia_comercial_agente_homologacao_orquestrador import executar_agente_com_memoria

router = APIRouter(
    prefix="/ia-comercial-agente-homologacao",
    tags=["IA Comercial Agente - Homologação"],
)


class ConsultaAgente(BaseModel):
    pergunta: str = Field(min_length=2, max_length=12000)
    conversa_id: UUID | None = None


def _configuracao_validada():
    config = carregar_ia_agente_homologacao_config()
    if not config.habilitada:
        raise HTTPException(status_code=404, detail="Agente experimental não habilitado neste ambiente.")
    if not config.pronta_para_homologacao:
        raise HTTPException(
            status_code=503,
            detail=(
                "Agente experimental bloqueado: deve operar fora da produção "
                "e obrigatoriamente em modo somente leitura operacional."
            ),
        )
    return config


@router.get("/status")
def status_agente_homologacao(
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    config = _configuracao_validada()
    return {
        "status": "ready_for_homologation",
        "nome": "IA Comercial CTI - Agente Experimental",
        "ambiente": config.ambiente,
        "somente_leitura_operacional": config.somente_leitura,
        "persistencia_ia": True,
        "schema_persistencia": "ia_homologacao",
        "modelo": config.modelo,
        "modelo_web": config.modelo_web,
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "perfil": usuario.tipo_usuario,
        },
        "garantias_operacionais": {
            "substitui_ia_atual": False,
            "altera_rotas_crm": False,
            "altera_dashboard": False,
            "altera_propostas_pedidos": False,
            "escreve_no_public": False,
            "escreve_apenas_area_ia": True,
        },
    }


@router.post("/consultar")
def consultar_agente_homologacao(
    payload: ConsultaAgente,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    config = _configuracao_validada()
    if usuario.tipo_usuario.strip().upper() != "ADMIN_MASTER":
        raise HTTPException(
            status_code=403,
            detail="A homologação inicial da nova IA é exclusiva do ADMIN_MASTER.",
        )

    try:
        resultado = executar_agente_com_memoria(
            pergunta=payload.pergunta.strip(),
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario,
            config=config,
            conversa_id=str(payload.conversa_id) if payload.conversa_id else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha no agente isolado de homologação: {type(exc).__name__}: {str(exc)[:300]}",
        ) from exc

    return {
        "status": "completed",
        "ambiente": config.ambiente,
        "somente_leitura_operacional": True,
        "persistencia_ia": True,
        "usuario": {"id": usuario.id, "perfil": usuario.tipo_usuario},
        **resultado,
    }
