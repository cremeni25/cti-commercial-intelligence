from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.ia_agente_homologacao_config import carregar_ia_agente_homologacao_config

router = APIRouter(
    prefix="/ia-comercial-agente-homologacao",
    tags=["IA Comercial Agente - Homologação"],
)


@router.get("/status")
def status_agente_homologacao(
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    config = carregar_ia_agente_homologacao_config()
    if not config.habilitada:
        raise HTTPException(status_code=404, detail="Agente experimental não habilitado neste ambiente.")
    if not config.pronta_para_homologacao:
        raise HTTPException(
            status_code=503,
            detail=(
                "Agente experimental bloqueado: deve operar fora da produção "
                "e obrigatoriamente em modo somente leitura."
            ),
        )

    return {
        "status": "ready_for_homologation",
        "nome": "IA Comercial CTI - Agente Experimental",
        "ambiente": config.ambiente,
        "somente_leitura": config.somente_leitura,
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
            "permite_escrita": False,
        },
    }
