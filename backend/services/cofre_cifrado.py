"""Envelope cifrado para dados comerciais que transitam pelo repositório público.

O repositório é público; planilhas da equipe (funil, negociações) nunca podem
ficar legíveis nele. O backend gera, uma única vez, um par de chaves X25519 e
guarda a chave privada no cofre PRIVADO do agente (Supabase Storage). Só a
chave pública é exposta. Quem prepara a carga cifra com ela; só o backend
consegue abrir.

Formato do envelope (JSON):
    {"versao": 1, "alg": "X25519-HKDF-SHA256-AES256GCM",
     "epk": <chave pública efêmera, b64>, "nonce": <b64>, "ct": <b64>,
     "rotulo": <nome lógico do conteúdo>}
O rótulo entra como dado associado: um envelope não pode ser trocado por outro.
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from services import cofre_agente

CAMINHO_CHAVE = "chaves/ingestao-x25519.json"
ALG = "X25519-HKDF-SHA256-AES256GCM"
_INFO = b"cti-ingestao-cifrada-v1"
_cache_privada: X25519PrivateKey | None = None


class EnvelopeInvalido(ValueError):
    """Envelope corrompido, de outra chave ou com rótulo trocado."""


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("ascii")


def _bytes_publicos(chave: X25519PublicKey) -> bytes:
    return chave.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _derivar(compartilhado: bytes, epk: bytes, destino: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=epk + destino, info=_INFO).derive(compartilhado)


def _chave_privada() -> X25519PrivateKey:
    """Lê do cofre ou cria na primeira vez (criação exclusiva evita corrida)."""
    global _cache_privada
    if _cache_privada is not None:
        return _cache_privada
    doc = cofre_agente.ler(CAMINHO_CHAVE)
    if not doc:
        nova = X25519PrivateKey.generate()
        bruto = nova.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
        cofre_agente.criar_exclusivo(CAMINHO_CHAVE, {"alg": ALG, "privada": _b64(bruto)})
        doc = cofre_agente.ler(CAMINHO_CHAVE)
    if not isinstance(doc, dict) or not doc.get("privada"):
        raise cofre_agente.CofreIndisponivel("Chave de ingestão indisponível no cofre.")
    _cache_privada = X25519PrivateKey.from_private_bytes(base64.b64decode(doc["privada"]))
    return _cache_privada


def chave_publica_b64() -> str:
    return _b64(_bytes_publicos(_chave_privada().public_key()))


def cifrar(conteudo: bytes, chave_publica: str, rotulo: str) -> dict[str, Any]:
    """Usado por quem prepara a carga (script local e testes); não precisa do cofre."""
    destino = base64.b64decode(chave_publica)
    efemera = X25519PrivateKey.generate()
    epk = _bytes_publicos(efemera.public_key())
    chave = _derivar(efemera.exchange(X25519PublicKey.from_public_bytes(destino)), epk, destino)
    nonce = os.urandom(12)
    ct = AESGCM(chave).encrypt(nonce, conteudo, rotulo.encode("utf-8"))
    return {"versao": 1, "alg": ALG, "rotulo": rotulo, "epk": _b64(epk), "nonce": _b64(nonce), "ct": _b64(ct)}


def abrir(envelope: dict[str, Any]) -> bytes:
    if not isinstance(envelope, dict) or envelope.get("alg") != ALG or envelope.get("versao") != 1:
        raise EnvelopeInvalido("Formato de envelope não reconhecido.")
    privada = _chave_privada()
    try:
        epk = base64.b64decode(envelope["epk"])
        destino = _bytes_publicos(privada.public_key())
        chave = _derivar(privada.exchange(X25519PublicKey.from_public_bytes(epk)), epk, destino)
        return AESGCM(chave).decrypt(base64.b64decode(envelope["nonce"]), base64.b64decode(envelope["ct"]), str(envelope.get("rotulo") or "").encode("utf-8"))
    except Exception as erro:
        raise EnvelopeInvalido("Não foi possível abrir o envelope (chave diferente ou conteúdo alterado).") from erro


def ler_envelope(caminho: str) -> dict[str, Any]:
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)
