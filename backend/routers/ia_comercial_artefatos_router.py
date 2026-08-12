from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from services.ia_comercial_artefatos import gerar_pdf_relatorio, gerar_svg_grafico


router = APIRouter(prefix="/ia-comercial-cti/artefatos", tags=["IA Comercial CTI — Artefatos"])


def _dados(resposta):
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _mensagem_do_usuario(mensagem_id: str, usuario: UsuarioAutenticado) -> dict:
    linhas = _dados(
        supabase.table("cti_ia_mensagens")
        .select("id,usuario_id,papel,conteudo,fontes,metadados,created_at")
        .eq("id", mensagem_id)
        .eq("usuario_id", usuario.id)
        .eq("papel", "assistant")
        .limit(1)
        .execute()
    )
    if not linhas:
        raise HTTPException(status_code=404, detail="Artefato não encontrado para este usuário.")
    return linhas[0]


def _artefatos(mensagem: dict) -> list[dict]:
    metadados = mensagem.get("metadados") or {}
    itens = metadados.get("artefatos") or []
    return [item for item in itens if isinstance(item, dict)]


@router.get("/{mensagem_id}/grafico.svg")
def baixar_grafico_svg(
    mensagem_id: str,
    indice: int = 0,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    mensagem = _mensagem_do_usuario(mensagem_id, usuario)
    graficos = [item for item in _artefatos(mensagem) if item.get("tipo") == "GRAFICO" and item.get("dados")]
    if indice < 0 or indice >= len(graficos):
        raise HTTPException(status_code=404, detail="Gráfico solicitado não encontrado nesta mensagem.")
    metadados = dict(mensagem.get("metadados") or {})
    demais = [item for item in _artefatos(mensagem) if item.get("tipo") != "GRAFICO"]
    metadados["artefatos"] = [graficos[indice], *demais]
    try:
        conteudo = gerar_svg_grafico(metadados)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=conteudo,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'attachment; filename="cti-grafico-{mensagem_id[:8]}-{indice + 1}.svg"'},
    )


@router.get("/{mensagem_id}/relatorio.pdf")
def baixar_relatorio_pdf(
    mensagem_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    mensagem = _mensagem_do_usuario(mensagem_id, usuario)
    if not any(item.get("tipo") == "RELATORIO_PDF" for item in _artefatos(mensagem)):
        raise HTTPException(status_code=404, detail="Esta mensagem não possui relatório PDF solicitado.")
    metadados = dict(mensagem.get("metadados") or {})
    if mensagem.get("fontes") and not metadados.get("fontes"):
        metadados["fontes"] = mensagem.get("fontes")
    conteudo = gerar_pdf_relatorio(
        conteudo=str(mensagem.get("conteudo") or ""),
        metadados=metadados,
        usuario_nome=usuario.nome or usuario.id,
    )
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="cti-relatorio-{mensagem_id[:8]}.pdf"'},
    )
