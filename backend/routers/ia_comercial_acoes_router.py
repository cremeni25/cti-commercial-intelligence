from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.pedidos_ciclo_router import AtualizarCicloRequest, atualizar_ciclo
from services.ia_comercial_dados_semanticos import _escopo_autorizado


router = APIRouter(prefix="/ia-comercial-cti/acoes", tags=["IA Comercial CTI - Ações Controladas"])

TIPOS_ACAO = {
    "CRIAR_ATIVIDADE_CRM",
    "ATUALIZAR_STATUS_ATIVIDADE",
    "ATUALIZAR_CICLO_PEDIDO",
}

STATUS_ATIVIDADE_PERMITIDOS = {"PENDENTE", "CONCLUIDA", "CONCLUÍDA", "CANCELADA"}


class ProporAcaoRequest(BaseModel):
    conversa_id: str
    tipo_acao: Literal[
        "CRIAR_ATIVIDADE_CRM",
        "ATUALIZAR_STATUS_ATIVIDADE",
        "ATUALIZAR_CICLO_PEDIDO",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)


class ConfirmarAcaoRequest(BaseModel):
    confirmar: bool = True


def _dados(resposta) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _conversa_autorizada(conversa_id: str, usuario: UsuarioAutenticado) -> None:
    linhas = _dados(
        supabase.table("cti_ia_conversas")
        .select("id")
        .eq("id", conversa_id)
        .eq("usuario_id", usuario.id)
        .limit(1)
        .execute()
    )
    if not linhas:
        raise HTTPException(status_code=404, detail="Conversa da IA Comercial não encontrada.")


def _por_id(registros: list[dict[str, Any]], registro_id: str) -> dict[str, Any] | None:
    alvo = str(registro_id or "").strip()
    return next((item for item in registros if str(item.get("id") or "") == alvo), None)


def _rotulo_cliente(cliente: dict[str, Any] | None) -> str:
    if not isinstance(cliente, dict):
        return "cliente selecionado"
    for campo in ("razao_social", "nome", "cliente", "nome_fantasia"):
        valor = str(cliente.get(campo) or "").strip()
        if valor:
            return valor
    return "cliente selecionado"


def _rotulo_pedido(pedido: dict[str, Any] | None) -> str:
    if not isinstance(pedido, dict):
        return "pedido selecionado"
    numero = str(pedido.get("numero") or "").strip()
    return numero or "pedido selecionado"


def _rotulo_atividade(atividade: dict[str, Any] | None) -> str:
    if not isinstance(atividade, dict):
        return "atividade selecionada"
    for campo in ("titulo", "descricao", "tipo"):
        valor = str(atividade.get(campo) or "").strip()
        if valor:
            return valor[:160]
    return "atividade selecionada"


def _resultado_publico(resultado: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mantém IDs técnicos na auditoria interna e os remove da resposta conversacional."""
    if not isinstance(resultado, dict):
        return resultado
    publico = dict(resultado)
    registro = publico.get("registro")
    if isinstance(registro, dict):
        registro_publico = {
            chave: valor
            for chave, valor in registro.items()
            if chave not in {
                "id",
                "cliente_id",
                "oportunidade_id",
                "pedido_id",
                "atividade_id",
                "usuario_id",
                "responsavel_id",
                "proposta_id",
                "aceite_id",
                "item_oportunidade_id",
            }
        }
        publico["registro"] = registro_publico
    return publico


def _normalizar_payload(
    tipo_acao: str,
    payload: dict[str, Any],
    usuario: UsuarioAutenticado,
) -> tuple[dict[str, Any], str]:
    escopo = _escopo_autorizado(usuario.id, usuario.tipo_usuario)

    if tipo_acao == "CRIAR_ATIVIDADE_CRM":
        cliente_id = str(payload.get("cliente_id") or "").strip()
        cliente = _por_id(escopo.get("clientes") or [], cliente_id)
        if not cliente_id or not cliente:
            raise HTTPException(status_code=403, detail="Cliente fora do escopo autorizado da IA Comercial.")

        oportunidade_id = str(payload.get("oportunidade_id") or "").strip() or None
        if oportunidade_id and not _por_id(escopo.get("oportunidades") or [], oportunidade_id):
            raise HTTPException(status_code=403, detail="Oportunidade fora do escopo autorizado da IA Comercial.")

        pedido_id = str(payload.get("pedido_id") or "").strip() or None
        pedido = _por_id(escopo.get("pedidos") or [], pedido_id) if pedido_id else None
        if pedido_id and not pedido:
            raise HTTPException(status_code=403, detail="Pedido fora do escopo autorizado da IA Comercial.")

        tipo = str(payload.get("tipo") or "ACOMPANHAMENTO").strip().upper()[:80]
        titulo = str(payload.get("titulo") or "Acompanhamento comercial").strip()[:240]
        descricao = str(payload.get("descricao") or "").strip()[:4000] or None
        data = str(payload.get("data") or "").strip()[:20] or None
        horario = str(payload.get("horario") or "").strip()[:20] or None
        normalizado = {
            "cliente_id": cliente_id,
            "oportunidade_id": oportunidade_id,
            "pedido_id": pedido_id,
            "usuario_id": usuario.id,
            "tipo": tipo,
            "titulo": titulo,
            "descricao": descricao,
            "data": data,
            "horario": horario,
            "status": "PENDENTE",
        }
        complemento_pedido = f" referente ao pedido {_rotulo_pedido(pedido)}" if pedido else ""
        resumo = f"Criar atividade {tipo} para o cliente {_rotulo_cliente(cliente)}{complemento_pedido}."
        return normalizado, resumo

    if tipo_acao == "ATUALIZAR_STATUS_ATIVIDADE":
        atividade_id = str(payload.get("atividade_id") or "").strip()
        atividade = _por_id(escopo.get("atividades") or [], atividade_id)
        if not atividade:
            raise HTTPException(status_code=403, detail="Atividade fora do escopo autorizado da IA Comercial.")
        status = str(payload.get("status") or "").strip().upper()
        if status not in STATUS_ATIVIDADE_PERMITIDOS:
            raise HTTPException(status_code=422, detail="Status de atividade não permitido para ação controlada.")
        if status == "CONCLUÍDA":
            status = "CONCLUIDA"
        cliente = _por_id(escopo.get("clientes") or [], str(atividade.get("cliente_id") or ""))
        resumo = f"Atualizar a atividade {_rotulo_atividade(atividade)}"
        if cliente:
            resumo += f" do cliente {_rotulo_cliente(cliente)}"
        resumo += f" para {status}."
        return {"atividade_id": atividade_id, "status": status}, resumo

    if tipo_acao == "ATUALIZAR_CICLO_PEDIDO":
        pedido_id = str(payload.get("pedido_id") or "").strip()
        pedido = _por_id(escopo.get("pedidos") or [], pedido_id)
        if not pedido:
            raise HTTPException(status_code=403, detail="Pedido fora do escopo autorizado da IA Comercial.")
        etapa = str(payload.get("etapa") or "").strip().upper()
        if etapa not in {"FATURADO", "ENTREGUE", "INSTALADO", "ENCERRADO"}:
            raise HTTPException(
                status_code=422,
                detail="A IA não pode confirmar CARRIER nem saltar para etapa não autorizada. Use o fluxo operacional oficial.",
            )
        normalizado = {
            "pedido_id": pedido_id,
            "etapa": etapa,
            "numero_nf": str(payload.get("numero_nf") or "").strip() or None,
            "numero_serie_nf": str(payload.get("numero_serie_nf") or "").strip() or None,
            "numero_serie_instalado": str(payload.get("numero_serie_instalado") or "").strip() or None,
            "observacao": str(payload.get("observacao") or "").strip()[:2000] or None,
        }
        cliente = _por_id(escopo.get("clientes") or [], str(pedido.get("cliente_id") or ""))
        resumo = f"Atualizar o ciclo do pedido {_rotulo_pedido(pedido)} para {etapa}"
        if cliente:
            resumo += f", cliente {_rotulo_cliente(cliente)}"
        resumo += ", usando as regras oficiais do CTI."
        return normalizado, resumo

    raise HTTPException(status_code=422, detail="Tipo de ação não permitido pela IA Comercial.")


def _carregar_proposta(acao_id: str, usuario: UsuarioAutenticado) -> dict[str, Any]:
    linhas = _dados(
        supabase.table("cti_ia_auditoria")
        .select("*")
        .eq("id", acao_id)
        .eq("usuario_id", usuario.id)
        .eq("acao", "IA008_ACAO_CONTROLADA")
        .limit(1)
        .execute()
    )
    if not linhas:
        raise HTTPException(status_code=404, detail="Ação controlada não encontrada.")
    return linhas[0]


def _executar(tipo_acao: str, payload: dict[str, Any], usuario: UsuarioAutenticado) -> dict[str, Any]:
    if tipo_acao == "CRIAR_ATIVIDADE_CRM":
        registro = {chave: valor for chave, valor in payload.items() if valor is not None}
        registro["usuario_id"] = usuario.id
        criado = _dados(supabase.table("cti_atividades").insert(registro).execute())
        if not criado:
            raise HTTPException(status_code=500, detail="Não foi possível criar a atividade controlada.")
        return {"tipo_acao": tipo_acao, "registro": criado[0]}

    if tipo_acao == "ATUALIZAR_STATUS_ATIVIDADE":
        atualizado = _dados(
            supabase.table("cti_atividades")
            .update({"status": payload["status"]})
            .eq("id", payload["atividade_id"])
            .execute()
        )
        if not atualizado:
            raise HTTPException(status_code=404, detail="Atividade não encontrada no momento da execução.")
        return {"tipo_acao": tipo_acao, "registro": atualizado[0]}

    if tipo_acao == "ATUALIZAR_CICLO_PEDIDO":
        dados = AtualizarCicloRequest(
            etapa=payload["etapa"],
            numero_nf=payload.get("numero_nf"),
            numero_serie_nf=payload.get("numero_serie_nf"),
            numero_serie_instalado=payload.get("numero_serie_instalado"),
            observacao=payload.get("observacao"),
        )
        resultado = atualizar_ciclo(payload["pedido_id"], dados)
        return {"tipo_acao": tipo_acao, "registro": resultado}

    raise HTTPException(status_code=422, detail="Tipo de ação não permitido pela IA Comercial.")


@router.post("")
def propor_acao(payload: ProporAcaoRequest, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _conversa_autorizada(payload.conversa_id, usuario)
    normalizado, resumo = _normalizar_payload(payload.tipo_acao, payload.payload, usuario)
    detalhes = {
        "versao": "IA-008-v1",
        "status": "PENDENTE_CONFIRMACAO",
        "tipo_acao": payload.tipo_acao,
        "payload": normalizado,
        "resumo": resumo,
        "confirmacao_explicita_obrigatoria": True,
        "idempotente": True,
        "executada": False,
    }
    criado = _dados(
        supabase.table("cti_ia_auditoria").insert(
            {
                "conversa_id": payload.conversa_id,
                "usuario_id": usuario.id,
                "acao": "IA008_ACAO_CONTROLADA",
                "detalhes": detalhes,
            }
        ).execute()
    )
    if not criado:
        raise HTTPException(status_code=500, detail="Não foi possível registrar a proposta de ação controlada.")
    registro = criado[0]
    return {
        "acao_id": registro.get("id"),
        "status": "PENDENTE_CONFIRMACAO",
        "tipo_acao": payload.tipo_acao,
        "resumo": resumo,
        "confirmacao_necessaria": True,
    }


@router.post("/{acao_id}/confirmar")
def confirmar_acao(
    acao_id: str,
    payload: ConfirmarAcaoRequest,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    proposta = _carregar_proposta(acao_id, usuario)
    detalhes = dict(proposta.get("detalhes") or {})
    resumo = str(detalhes.get("resumo") or "Ação controlada executada.")

    if detalhes.get("status") == "EXECUTADA":
        return {
            "acao_id": acao_id,
            "status": "EXECUTADA",
            "idempotencia": "JA_EXECUTADA_SEM_REPETICAO",
            "resumo": resumo,
            "resultado": _resultado_publico(detalhes.get("resultado")),
        }
    if detalhes.get("status") == "CANCELADA":
        raise HTTPException(status_code=409, detail="A ação foi cancelada e não pode mais ser executada.")
    if detalhes.get("status") != "PENDENTE_CONFIRMACAO":
        raise HTTPException(status_code=409, detail="A ação não está disponível para confirmação.")
    if not payload.confirmar:
        raise HTTPException(status_code=422, detail="Confirmação explícita é obrigatória para executar a ação.")

    tipo_acao = str(detalhes.get("tipo_acao") or "")
    payload_normalizado, resumo_atualizado = _normalizar_payload(
        tipo_acao,
        dict(detalhes.get("payload") or {}),
        usuario,
    )
    resultado = _executar(tipo_acao, payload_normalizado, usuario)

    detalhes.update(
        {
            "status": "EXECUTADA",
            "executada": True,
            "resultado": resultado,
            "resumo": resumo_atualizado,
            "confirmada_por_usuario_id": usuario.id,
        }
    )
    supabase.table("cti_ia_auditoria").update({"detalhes": detalhes}).eq("id", acao_id).eq("usuario_id", usuario.id).execute()
    return {
        "acao_id": acao_id,
        "status": "EXECUTADA",
        "resumo": resumo_atualizado,
        "resultado": _resultado_publico(resultado),
    }


@router.post("/{acao_id}/cancelar")
def cancelar_acao(acao_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    proposta = _carregar_proposta(acao_id, usuario)
    detalhes = dict(proposta.get("detalhes") or {})
    if detalhes.get("status") == "EXECUTADA":
        raise HTTPException(status_code=409, detail="Ação já executada não pode ser cancelada por este endpoint.")
    detalhes["status"] = "CANCELADA"
    detalhes["executada"] = False
    supabase.table("cti_ia_auditoria").update({"detalhes": detalhes}).eq("id", acao_id).eq("usuario_id", usuario.id).execute()
    return {"acao_id": acao_id, "status": "CANCELADA"}
