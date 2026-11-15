"""Acervo comercial: carteiras, transferência que preserva a autoria, exportação e cópias."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.github_oidc import TokenInvalido, validar_token_workflow
from services import acervo_comercial as acervo
from services.cofre_agente import CofreIndisponivel

router = APIRouter(tags=["Acervo comercial"])

ROTA_BACKUP_AGENDADO = "/interno/acervo/backup"
PUBLICO_OIDC = "cti-acervo-backup"
WORKFLOW_BACKUP = "acervo-backup.yml"
TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _gestao(usuario: UsuarioAutenticado) -> None:
    if usuario.tipo_usuario == "ADMIN_MASTER" or (usuario.tipo_usuario == "DIRETOR_VIENA_SP" and bool((usuario.permissoes or {}).get("acesso_total"))):
        return
    raise HTTPException(status_code=403, detail="Acervo comercial disponível somente para a gestão.")


class Transferencia(BaseModel):
    de_usuario_id: str = Field(min_length=1)
    para_usuario_id: str = Field(min_length=1)
    motivo: str = Field(default="", max_length=300)


@router.get("/crm-seguro/acervo/carteiras")
def carteiras(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _gestao(usuario)
    return acervo.carteiras()


@router.post("/crm-seguro/acervo/transferir")
def transferir(dados: Transferencia, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _gestao(usuario)
    try:
        return acervo.transferir_carteira(dados.de_usuario_id, dados.para_usuario_id, dados.motivo.strip(), str(usuario.id))
    except acervo.AcervoErro as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except CofreIndisponivel as erro:
        raise HTTPException(status_code=503, detail="Não foi possível guardar a cópia de segurança antes da transferência; nada foi alterado.") from erro


@router.get("/crm-seguro/acervo/exportacao")
def exportacao(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _gestao(usuario)
    conteudo, _ = acervo.gerar_exportacao()
    return Response(conteudo, media_type=TIPO_XLSX, headers={"Content-Disposition": 'attachment; filename="acervo-comercial-cti.xlsx"'})


@router.get("/crm-seguro/acervo/backups")
def backups(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _gestao(usuario)
    try:
        return {"backups": acervo.listar_backups()}
    except CofreIndisponivel as erro:
        raise HTTPException(status_code=503, detail="Cofre indisponível no momento.") from erro


@router.post("/crm-seguro/acervo/backups", status_code=201)
def novo_backup(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _gestao(usuario)
    try:
        registro = acervo.salvar_backup(f"cópia manual por {usuario.nome or usuario.email}")
        from services.cofre_agente import caminho, url_assinada

        return {**registro, "url": url_assinada(caminho(acervo.PASTA_BACKUP, registro["arquivo"]), 3600)}
    except CofreIndisponivel as erro:
        raise HTTPException(status_code=503, detail="Cofre indisponível no momento.") from erro


@router.post(ROTA_BACKUP_AGENDADO)
def backup_agendado(authorization: str | None = Header(default=None)):
    """Cópia semanal automática, disparada pelo workflow acervo-backup.yml (token OIDC do GitHub)."""
    partes = (authorization or "").split(" ", 1)
    try:
        if len(partes) != 2 or partes[0].lower() != "bearer":
            raise TokenInvalido("sem token")
        validar_token_workflow(partes[1].strip(), publico=PUBLICO_OIDC, workflow=WORKFLOW_BACKUP)
    except TokenInvalido as erro:
        raise HTTPException(status_code=401, detail="Disparo agendado não autorizado.") from erro
    registro = acervo.salvar_backup("cópia semanal automática")
    return {"arquivo": registro["arquivo"], "totais": registro["totais"]}
