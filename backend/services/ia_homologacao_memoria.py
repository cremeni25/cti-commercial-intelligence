from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import UUID

from core.supabase_client import supabase

SCHEMA = "ia_homologacao"


def _tabela(nome: str):
    return supabase.schema(SCHEMA).table(nome)


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def abrir_conversa(usuario_id: str, conversa_id: str | None, pergunta: str) -> str:
    if conversa_id:
        UUID(conversa_id)
        resposta = (
            _tabela("conversas")
            .select("id,usuario_id,status")
            .eq("id", conversa_id)
            .eq("usuario_id", usuario_id)
            .maybe_single()
            .execute()
        )
        registro = resposta.data
        if not registro or registro.get("status") != "ATIVA":
            raise ValueError("Conversa de homologação inexistente, encerrada ou pertencente a outro usuário.")
        return str(registro["id"])

    titulo = pergunta.strip().replace("\n", " ")[:120]
    resposta = (
        _tabela("conversas")
        .insert({
            "usuario_id": usuario_id,
            "titulo": titulo,
            "status": "ATIVA",
            "metadados": {"ambiente": "homologacao"},
        })
        .execute()
    )
    if not resposta.data:
        raise RuntimeError("Não foi possível criar a conversa de homologação.")
    return str(resposta.data[0]["id"])


def carregar_memoria(conversa_id: str, usuario_id: str, limite: int = 20) -> list[dict[str, str]]:
    resposta = (
        _tabela("mensagens")
        .select("papel,conteudo,created_at")
        .eq("conversa_id", conversa_id)
        .eq("usuario_id", usuario_id)
        .order("created_at", desc=True)
        .limit(max(1, min(limite, 50)))
        .execute()
    )
    registros = list(reversed(resposta.data or []))
    return [
        {"papel": str(item.get("papel") or ""), "conteudo": str(item.get("conteudo") or "")}
        for item in registros
        if item.get("papel") in {"user", "assistant"} and item.get("conteudo")
    ]


def registrar_mensagem(
    conversa_id: str,
    usuario_id: str,
    papel: str,
    conteudo: str,
    ferramentas: list[dict[str, Any]] | None = None,
    fontes: list[dict[str, Any]] | None = None,
) -> str:
    resposta = (
        _tabela("mensagens")
        .insert({
            "conversa_id": conversa_id,
            "usuario_id": usuario_id,
            "papel": papel,
            "conteudo": conteudo,
            "ferramentas": ferramentas or [],
            "fontes": fontes or [],
        })
        .execute()
    )
    if not resposta.data:
        raise RuntimeError("Não foi possível registrar a mensagem da homologação.")
    _tabela("conversas").update({"updated_at": _agora_iso()}).eq("id", conversa_id).execute()
    return str(resposta.data[0]["id"])


def iniciar_execucao(conversa_id: str, usuario_id: str, pergunta: str, metadados: dict[str, Any]) -> tuple[str, float]:
    resposta = (
        _tabela("execucoes")
        .insert({
            "conversa_id": conversa_id,
            "usuario_id": usuario_id,
            "pergunta": pergunta,
            "status": "INICIADA",
            "metadados": metadados,
        })
        .execute()
    )
    if not resposta.data:
        raise RuntimeError("Não foi possível iniciar a auditoria da execução.")
    execucao_id = str(resposta.data[0]["id"])
    registrar_auditoria(usuario_id, "EXECUCAO_INICIADA", "execucoes", execucao_id, depois={"conversa_id": conversa_id})
    return execucao_id, perf_counter()


def concluir_execucao(
    execucao_id: str,
    usuario_id: str,
    inicio: float,
    ferramentas: list[dict[str, Any]],
    metadados: dict[str, Any],
) -> None:
    duracao_ms = int((perf_counter() - inicio) * 1000)
    _tabela("execucoes").update({
        "ferramentas_executadas": ferramentas,
        "status": "CONCLUIDA",
        "finalizada_em": _agora_iso(),
        "duracao_ms": duracao_ms,
        "metadados": metadados,
    }).eq("id", execucao_id).execute()
    registrar_auditoria(
        usuario_id,
        "EXECUCAO_CONCLUIDA",
        "execucoes",
        execucao_id,
        depois={"duracao_ms": duracao_ms, "ferramentas": len(ferramentas)},
    )


def falhar_execucao(execucao_id: str, usuario_id: str, inicio: float, erro: Exception) -> None:
    duracao_ms = int((perf_counter() - inicio) * 1000)
    descricao = f"{type(erro).__name__}: {str(erro)[:1000]}"
    _tabela("execucoes").update({
        "status": "FALHA",
        "erro": descricao,
        "finalizada_em": _agora_iso(),
        "duracao_ms": duracao_ms,
    }).eq("id", execucao_id).execute()
    registrar_auditoria(
        usuario_id,
        "EXECUCAO_FALHA",
        "execucoes",
        execucao_id,
        depois={"duracao_ms": duracao_ms, "erro": descricao},
    )


def registrar_fontes(conversa_id: str, mensagem_id: str, fontes: list[dict[str, str]]) -> None:
    registros = []
    for fonte in fontes:
        url = str(fonte.get("url") or "").strip()
        if not url:
            continue
        dominio = url.split("//", 1)[-1].split("/", 1)[0].lower()
        registros.append({
            "conversa_id": conversa_id,
            "mensagem_id": mensagem_id,
            "url": url,
            "titulo": fonte.get("descricao"),
            "dominio": dominio,
            "metadados": {"tipo": fonte.get("tipo", "WEB")},
        })
    if registros:
        _tabela("fontes_web").insert(registros).execute()


def registrar_auditoria(
    usuario_id: str | None,
    evento: str,
    entidade: str | None = None,
    entidade_id: str | None = None,
    antes: dict[str, Any] | None = None,
    depois: dict[str, Any] | None = None,
    contexto: dict[str, Any] | None = None,
) -> None:
    _tabela("auditoria").insert({
        "usuario_id": usuario_id,
        "evento": evento,
        "entidade": entidade,
        "entidade_id": entidade_id,
        "origem": "IA_HOMOLOGACAO",
        "antes": antes,
        "depois": depois,
        "contexto": contexto or {},
    }).execute()
