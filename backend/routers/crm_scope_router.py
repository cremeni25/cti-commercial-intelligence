from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_app_proposta_envio_router import EnviarPropostaRequest, enviar_proposta_por_email
from routers.crm_core_extension import nucleo_comercial
from routers.crm_router import (
    OportunidadeUpdate,
    PedidoUpdate,
    PropostaUpdate,
    atualizar_oportunidade,
    atualizar_pedido,
    atualizar_proposta,
    obter_oportunidade,
    obter_pedido,
    obter_proposta,
)
from routers.documentos_comerciais_listagem_router import (
    listar_pedidos_operacionais,
    listar_propostas_operacionais,
)
from routers.pedidos_operacionais_router import (
    ConverterPedidoOperacionalRequest,
    converter_pedido_operacional,
)
from routers.propostas_consulta_router import consultar_proposta
from routers.propostas_pedidos_router import (
    SolicitarAceiteRequest,
    emitir_proposta,
    solicitar_aceite,
)

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro"])

PERFIS_ESCOPO_PROPRIO = {
    "REPRES_REGIAO_01",
    "REPRES_REGIAO_02",
    "INDICADOR_VIENA_SP",
}


def _visao_consolidada(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP"
        and bool(usuario.permissoes.get("acesso_total"))
    )


def _usa_escopo_proprio(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario in PERFIS_ESCOPO_PROPRIO


def _filtrar_por_usuario(registros: list[dict], usuario: UsuarioAutenticado) -> list[dict]:
    if _visao_consolidada(usuario):
        return registros
    if not _usa_escopo_proprio(usuario):
        # USUARIO_CTI permanece com o comportamento atual até definição
        # específica de governança (caso administrativo da Gessica).
        return registros
    resultado: list[dict] = []
    for item in registros:
        try:
            responsavel = _responsavel_efetivo(item)
        except HTTPException:
            responsavel = str(item.get("responsavel_id") or "")
        if responsavel == str(usuario.id):
            resultado.append(item)
    return resultado


def _responsavel_efetivo(registro: dict) -> str:
    responsavel = str(registro.get("responsavel_id") or "").strip()
    if responsavel:
        return responsavel
    oportunidade_id = str(registro.get("oportunidade_id") or "").strip()
    if oportunidade_id:
        oportunidade = obter_oportunidade(oportunidade_id)
        return str(oportunidade.get("responsavel_id") or "").strip()
    return ""


def _exigir_acesso(registro: dict, usuario: UsuarioAutenticado) -> dict:
    if _visao_consolidada(usuario) or not _usa_escopo_proprio(usuario):
        return registro
    if _responsavel_efetivo(registro) == str(usuario.id):
        return registro
    # 404 evita revelar a existência de um registro fora do escopo do usuário.
    raise HTTPException(status_code=404, detail="Registro comercial não encontrado")


def _impedir_transferencia(responsavel_id: str | None, usuario: UsuarioAutenticado) -> None:
    if not _usa_escopo_proprio(usuario) or responsavel_id is None:
        return
    if str(responsavel_id) != str(usuario.id):
        raise HTTPException(status_code=403, detail="Não é permitido transferir o responsável deste registro")


def _proposta_autorizada(proposta_id: str, usuario: UsuarioAutenticado) -> dict:
    return _exigir_acesso(obter_proposta(proposta_id), usuario)


@router.get("/nucleo-comercial")
def nucleo_comercial_seguro(
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Núcleo canônico com enforcement de escopo baseado no login autenticado."""
    return _filtrar_por_usuario(nucleo_comercial(), usuario)


@router.get("/propostas")
def listar_propostas_seguras(
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return _filtrar_por_usuario(listar_propostas_operacionais(), usuario)


@router.get("/pedidos")
def listar_pedidos_seguros(
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return _filtrar_por_usuario(listar_pedidos_operacionais(), usuario)


@router.get("/oportunidades/{oportunidade_id}")
def obter_oportunidade_segura(
    oportunidade_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return _exigir_acesso(obter_oportunidade(oportunidade_id), usuario)


@router.put("/oportunidades/{oportunidade_id}")
def atualizar_oportunidade_segura(
    oportunidade_id: str,
    oportunidade: OportunidadeUpdate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_acesso(obter_oportunidade(oportunidade_id), usuario)
    return atualizar_oportunidade(oportunidade_id, oportunidade)


@router.get("/propostas/{proposta_id}")
def obter_proposta_segura(
    proposta_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return _proposta_autorizada(proposta_id, usuario)


@router.get("/propostas/{proposta_id}/pacote")
def consultar_proposta_segura(
    proposta_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _proposta_autorizada(proposta_id, usuario)
    return consultar_proposta(proposta_id)


@router.post("/propostas/{proposta_id}/emitir")
def emitir_proposta_segura(
    proposta_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _proposta_autorizada(proposta_id, usuario)
    return emitir_proposta(proposta_id)


@router.post("/propostas/{proposta_id}/aceites")
def solicitar_aceite_seguro(
    proposta_id: str,
    dados: SolicitarAceiteRequest,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _proposta_autorizada(proposta_id, usuario)
    return solicitar_aceite(proposta_id, dados)


@router.post("/propostas/{proposta_id}/enviar-email")
def enviar_proposta_email_seguro(
    proposta_id: str,
    dados: EnviarPropostaRequest,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _proposta_autorizada(proposta_id, usuario)
    return enviar_proposta_por_email(proposta_id, dados)


@router.post("/propostas/{proposta_id}/converter-pedido-operacional")
def converter_pedido_operacional_seguro(
    proposta_id: str,
    dados: ConverterPedidoOperacionalRequest,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    proposta = _proposta_autorizada(proposta_id, usuario)
    if _usa_escopo_proprio(usuario):
        # Nunca confia no responsável enviado pelo navegador de um perfil regional.
        dados = dados.model_copy(update={"responsavel_id": str(usuario.id)})
    elif dados.responsavel_id is None:
        responsavel = _responsavel_efetivo(proposta)
        dados = dados.model_copy(update={"responsavel_id": responsavel or None})
    return converter_pedido_operacional(proposta_id, dados)


@router.put("/propostas/{proposta_id}")
def atualizar_proposta_segura(
    proposta_id: str,
    proposta: PropostaUpdate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _proposta_autorizada(proposta_id, usuario)
    _impedir_transferencia(proposta.responsavel_id, usuario)
    return atualizar_proposta(proposta_id, proposta)


@router.get("/pedidos/{pedido_id}")
def obter_pedido_seguro(
    pedido_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return _exigir_acesso(obter_pedido(pedido_id), usuario)


@router.put("/pedidos/{pedido_id}")
def atualizar_pedido_seguro(
    pedido_id: str,
    pedido: PedidoUpdate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_acesso(obter_pedido(pedido_id), usuario)
    _impedir_transferencia(pedido.responsavel_id, usuario)
    return atualizar_pedido(pedido_id, pedido)
