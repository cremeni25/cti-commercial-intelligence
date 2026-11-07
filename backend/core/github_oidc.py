"""Autenticação de chamadas agendadas do GitHub Actions, sem segredo manual.

O GitHub emite para cada execução de workflow um token de identidade (OIDC)
assinado com as chaves públicas dele. Aqui o token só é aceito se TODAS as
condições valerem:

- emitido pelo GitHub (``iss``) para este público (``aud``);
- vindo DESTE repositório, na branch ``main``, pelo workflow esperado;
- disparado por agenda ou execução manual do próprio repositório.

Assim ninguém precisa criar, copiar ou rotacionar segredo: um PR de fork, outro
repositório ou outro workflow não consegue disparar o envio.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

EMISSOR = "https://token.actions.githubusercontent.com"
JWKS_URL = f"{EMISSOR}/.well-known/jwks"
EVENTOS_PERMITIDOS = {"schedule", "workflow_dispatch"}


class TokenInvalido(Exception):
    pass


def repositorio_esperado() -> str:
    return os.getenv("CTI_GITHUB_REPOSITORIO", "cremeni25/cti-commercial-intelligence").strip()


@lru_cache(maxsize=1)
def _cliente_jwks():
    from jwt import PyJWKClient

    return PyJWKClient(JWKS_URL, cache_keys=True, lifespan=3600, timeout=10)


def _chave_assinatura(token: str):
    return _cliente_jwks().get_signing_key_from_jwt(token).key


def validar_token_workflow(token: str, *, publico: str, workflow: str) -> dict[str, Any]:
    import jwt

    try:
        claims = jwt.decode(
            token,
            _chave_assinatura(token),
            algorithms=["RS256"],
            audience=publico,
            issuer=EMISSOR,
            options={"require": ["exp", "iat", "iss", "aud", "repository", "ref", "workflow_ref"]},
            leeway=30,
        )
    except Exception as erro:  # assinatura, validade, emissor ou público
        raise TokenInvalido(f"Token do GitHub rejeitado: {type(erro).__name__}") from erro
    repositorio = repositorio_esperado()
    esperado_ref = f"{repositorio}/.github/workflows/{workflow}@refs/heads/main"
    if claims.get("repository") != repositorio:
        raise TokenInvalido("Token de outro repositório.")
    if claims.get("ref") != "refs/heads/main" or claims.get("workflow_ref") != esperado_ref:
        raise TokenInvalido("Token fora do workflow e da branch autorizados.")
    if claims.get("event_name") not in EVENTOS_PERMITIDOS:
        raise TokenInvalido("Evento do GitHub não autorizado para este disparo.")
    return claims
