"""Cofre do Agente: armazenamento auto-provisionado, sem migração manual.

Guarda o estado operacional do Agente de Inteligência em documentos JSON num
bucket PRIVADO do Supabase Storage (``cti-agente``), que o próprio backend cria
na primeira utilização com a chave de serviço já configurada no Render.

Nada aqui é dado comercial de origem: só ajustes de alertas, inscrições de
celular, chaves do push e marcas de envio. Por isso o formato documento é
suficiente e evita qualquer passo manual de banco.

Concorrência: cada documento pertence a um único usuário (ou é de sistema), e as
gravações são leitura-modificação-escrita do mesmo dono — adequado ao volume de
uma equipe comercial. Marcas de "uma vez por dia" usam criação exclusiva
(``upsert=false``), atômica no Storage.
"""
from __future__ import annotations

import json
import re
from typing import Any

BUCKET = "cti-agente"
_PROVISIONADO = False
_SEGMENTO = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


class CofreIndisponivel(RuntimeError):
    """O Storage não respondeu; o recurso dependente segue desligado com aviso."""


def _supabase():
    from core.supabase_client import supabase

    return supabase


def caminho(*partes: str) -> str:
    """Monta um caminho seguro: cada segmento é validado (sem ``..`` nem barras)."""
    segmentos = [str(p) for p in partes]
    if not segmentos or any(not _SEGMENTO.match(s) or s in {".", ".."} for s in segmentos):
        raise ValueError("Caminho inválido no cofre do agente.")
    return "/".join(segmentos)


def provisionar() -> None:
    """Cria o bucket privado na primeira vez; idempotente."""
    global _PROVISIONADO
    if _PROVISIONADO:
        return
    storage = _supabase().storage
    try:
        storage.get_bucket(BUCKET)
    except Exception:
        try:
            storage.create_bucket(BUCKET, options={"public": False})
        except Exception as erro:
            # Corrida entre instâncias: outra pode ter criado agora.
            try:
                storage.get_bucket(BUCKET)
            except Exception:
                raise CofreIndisponivel(str(erro)) from erro
    _PROVISIONADO = True


def _nao_encontrado(erro: Exception) -> bool:
    texto = str(erro).lower()
    return any(t in texto for t in ("not found", "not_found", "404", "does not exist", "object not found"))


def ler(caminho_doc: str, padrao: Any = None) -> Any:
    provisionar()
    try:
        bruto = _supabase().storage.from_(BUCKET).download(caminho_doc)
    except Exception as erro:
        if _nao_encontrado(erro):
            return padrao
        raise CofreIndisponivel(str(erro)) from erro
    try:
        return json.loads(bytes(bruto or b"").decode("utf-8") or "null")
    except ValueError:
        return padrao


def gravar(caminho_doc: str, dados: Any) -> None:
    provisionar()
    conteudo = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
    try:
        _supabase().storage.from_(BUCKET).upload(caminho_doc, conteudo, {"content-type": "application/json", "upsert": "true"})
    except Exception as erro:
        raise CofreIndisponivel(str(erro)) from erro


def criar_exclusivo(caminho_doc: str, dados: Any) -> bool:
    """Cria o documento só se ainda não existir. True = criado agora."""
    provisionar()
    conteudo = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
    try:
        _supabase().storage.from_(BUCKET).upload(caminho_doc, conteudo, {"content-type": "application/json", "upsert": "false"})
        return True
    except Exception as erro:
        texto = str(erro).lower()
        if any(t in texto for t in ("exists", "duplicate", "409", "conflict")):
            return False
        raise CofreIndisponivel(str(erro)) from erro


def listar(pasta: str) -> list[str]:
    provisionar()
    try:
        itens = _supabase().storage.from_(BUCKET).list(pasta, {"limit": 1000}) or []
    except Exception as erro:
        if _nao_encontrado(erro):
            return []
        raise CofreIndisponivel(str(erro)) from erro
    return [str(item.get("name")) for item in itens if isinstance(item, dict) and str(item.get("name") or "").endswith(".json")]


def ler_pasta(pasta: str) -> dict[str, Any]:
    """Todos os documentos JSON de uma pasta, por nome de arquivo."""
    return {nome: ler(f"{pasta}/{nome}") for nome in listar(pasta)}


def gravar_binario(caminho_doc: str, conteudo: bytes, tipo: str) -> None:
    provisionar()
    try:
        _supabase().storage.from_(BUCKET).upload(caminho_doc, conteudo, {"content-type": tipo, "upsert": "true"})
    except Exception as erro:
        raise CofreIndisponivel(str(erro)) from erro


def ler_binario(caminho_doc: str) -> bytes | None:
    """Arquivo binário do bucket privado; None quando ainda não existe."""
    provisionar()
    try:
        bruto = _supabase().storage.from_(BUCKET).download(caminho_doc)
    except Exception as erro:
        if _nao_encontrado(erro):
            return None
        raise CofreIndisponivel(str(erro)) from erro
    return bytes(bruto or b"")


def url_assinada(caminho_doc: str, segundos: int = 3600) -> str | None:
    """Link temporário para um arquivo do bucket privado (nunca público)."""
    provisionar()
    try:
        resposta = _supabase().storage.from_(BUCKET).create_signed_url(caminho_doc, segundos)
    except Exception:
        return None
    if isinstance(resposta, dict):
        return resposta.get("signedURL") or resposta.get("signedUrl") or resposta.get("signed_url")
    return getattr(resposta, "signed_url", None) or getattr(resposta, "signedURL", None)
