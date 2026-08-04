from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from services.ia_comercial_cti import IAComercialOpenAIError, contexto_comercial, gerar_resposta

router = APIRouter(prefix="/ia-comercial-cti", tags=["IA Comercial CTI"])


class NovaConversa(BaseModel):
    titulo: str = Field(default="Nova conversa", max_length=120)


class NovaMensagem(BaseModel):
    mensagem: str = Field(min_length=1, max_length=12000)


def _dados(resposta):
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _conversa_do_usuario(conversa_id: str, usuario: UsuarioAutenticado) -> dict:
    resposta = (
        supabase.table("cti_ia_conversas")
        .select("*")
        .eq("id", conversa_id)
        .eq("usuario_id", usuario.id)
        .limit(1)
        .execute()
    )
    linhas = _dados(resposta)
    if not linhas:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    return linhas[0]


@router.get("/status")
def status_ia(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return {
        "status": "ready",
        "nome": "IA Comercial CTI",
        "modo": "leitura_e_analise",
        "usuario": {"id": usuario.id, "nome": usuario.nome, "perfil": usuario.tipo_usuario},
    }


@router.get("/conversas")
def listar_conversas(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return _dados(
        supabase.table("cti_ia_conversas")
        .select("*")
        .eq("usuario_id", usuario.id)
        .order("updated_at", desc=True)
        .execute()
    )


@router.post("/conversas")
def criar_conversa(payload: NovaConversa, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    titulo = payload.titulo.strip() or "Nova conversa"
    criado = _dados(
        supabase.table("cti_ia_conversas")
        .insert({"usuario_id": usuario.id, "titulo": titulo, "status": "ATIVA"})
        .execute()
    )
    if not criado:
        raise HTTPException(status_code=500, detail="Não foi possível criar a conversa.")
    return criado[0]


@router.get("/conversas/{conversa_id}/mensagens")
def listar_mensagens(conversa_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _conversa_do_usuario(conversa_id, usuario)
    return _dados(
        supabase.table("cti_ia_mensagens")
        .select("*")
        .eq("conversa_id", conversa_id)
        .order("created_at")
        .execute()
    )


@router.post("/conversas/{conversa_id}/mensagens")
def enviar_mensagem(
    conversa_id: str,
    payload: NovaMensagem,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    conversa = _conversa_do_usuario(conversa_id, usuario)
    mensagem = payload.mensagem.strip()

    mensagens_anteriores = _dados(
        supabase.table("cti_ia_mensagens")
        .select("papel,conteudo")
        .eq("conversa_id", conversa_id)
        .order("created_at")
        .limit(40)
        .execute()
    )
    historico = [
        {"role": str(item.get("papel") or "user"), "content": str(item.get("conteudo") or "")}
        for item in mensagens_anteriores
        if item.get("conteudo")
    ]

    supabase.table("cti_ia_mensagens").insert({
        "conversa_id": conversa_id,
        "usuario_id": usuario.id,
        "papel": "user",
        "conteudo": mensagem,
        "fontes": [],
        "metadados": {},
    }).execute()

    try:
        contexto = contexto_comercial(usuario.id, usuario.tipo_usuario)
        resposta_texto, metadados = gerar_resposta(mensagem, historico, contexto)
    except IAComercialOpenAIError as exc:
        supabase.table("cti_ia_auditoria").insert({
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "acao": "ERRO_OPENAI",
            "detalhes": {
                "codigo": exc.codigo,
                "erro": exc.detalhe_tecnico,
            },
        }).execute()
        raise HTTPException(status_code=502, detail=exc.mensagem_publica) from exc
    except Exception as exc:
        supabase.table("cti_ia_auditoria").insert({
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "acao": "ERRO_GERACAO_RESPOSTA",
            "detalhes": {"tipo": type(exc).__name__, "erro": str(exc)[:500]},
        }).execute()
        raise HTTPException(
            status_code=502,
            detail="O núcleo da IA encontrou uma falha interna antes de concluir a resposta. A ocorrência foi registrada na auditoria.",
        ) from exc

    fontes = [{"tipo": "CTI", "descricao": "Clientes, oportunidades, propostas e pedidos autorizados."}]
    assistente = _dados(
        supabase.table("cti_ia_mensagens").insert({
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "papel": "assistant",
            "conteudo": resposta_texto,
            "fontes": fontes,
            "metadados": metadados,
        }).execute()
    )

    agora = datetime.now(timezone.utc).isoformat()
    atualizacao = {"updated_at": agora}
    if str(conversa.get("titulo") or "") == "Nova conversa":
        atualizacao["titulo"] = mensagem[:80]
    supabase.table("cti_ia_conversas").update(atualizacao).eq("id", conversa_id).execute()
    supabase.table("cti_ia_auditoria").insert({
        "conversa_id": conversa_id,
        "usuario_id": usuario.id,
        "acao": "RESPOSTA_GERADA",
        "detalhes": metadados,
    }).execute()

    return assistente[0] if assistente else {
        "conversa_id": conversa_id,
        "papel": "assistant",
        "conteudo": resposta_texto,
        "fontes": fontes,
        "metadados": metadados,
    }
