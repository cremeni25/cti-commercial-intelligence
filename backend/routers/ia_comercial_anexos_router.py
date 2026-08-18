from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.ia_comercial_cti_router import (
    _HISTORICO_MAX_MENSAGENS,
    _conversa_do_usuario,
    _historico_conversacional,
    _mensagem_com_contexto_temporal,
    _renderizar_plano_validado,
    _tratar_acao_controlada,
)
from services.ia_comercial_agente_crm import gerar_resposta_agente
from services.ia_comercial_anexos import (
    AnexoIAError,
    MAX_ANEXOS,
    MAX_TOTAL_BYTES,
    construir_contexto_anexos,
    metadados_publicos_anexos,
    preparar_anexo,
)
from services.ia_comercial_auditoria_evidencial import construir_auditoria_evidencial
from services.ia_comercial_conhecimento_semantico import persistir_anexos_como_conhecimento
from services.ia_comercial_cti import IAComercialOpenAIError
from services.ia_comercial_sintese_crm import sintetizar_fatos_execucao


router = APIRouter(prefix="/ia-comercial-cti", tags=["IA Comercial CTI — Anexos"])


def _dados(resposta):
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _registrar_usuario_com_anexos(
    conversa_id: str,
    usuario: UsuarioAutenticado,
    mensagem: str,
    anexos_publicos: list[dict],
) -> None:
    supabase.table("cti_ia_mensagens").insert(
        {
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "papel": "user",
            "conteudo": mensagem,
            "fontes": [],
            "metadados": {
                "anexos": anexos_publicos,
                "controle_anexos": "temporarios_nao_publicados",
            },
        }
    ).execute()


@router.post("/conversas/{conversa_id}/mensagens-anexos")
async def enviar_mensagem_com_anexos(
    conversa_id: str,
    mensagem: str = Form(...),
    arquivos: list[UploadFile] = File(...),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    conversa = _conversa_do_usuario(conversa_id, usuario)
    texto_usuario = mensagem.strip()
    if not texto_usuario:
        raise HTTPException(status_code=422, detail="Escreva uma instrução para os anexos.")
    if not arquivos:
        raise HTTPException(status_code=422, detail="Nenhum anexo recebido.")
    if len(arquivos) > MAX_ANEXOS:
        raise HTTPException(status_code=413, detail=f"Envie no máximo {MAX_ANEXOS} arquivos por interação.")

    anexos_processados: list[dict] = []
    total_bytes = 0
    try:
        for arquivo in arquivos:
            conteudo = await arquivo.read()
            total_bytes += len(conteudo)
            if total_bytes > MAX_TOTAL_BYTES:
                raise AnexoIAError("Os anexos desta interação excedem 30 MB no total.")
            anexos_processados.append(
                preparar_anexo(
                    arquivo.filename or "arquivo",
                    arquivo.content_type,
                    conteudo,
                )
            )
    except AnexoIAError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    anexos_publicos = metadados_publicos_anexos(anexos_processados)
    historico = _historico_conversacional(conversa_id, usuario)
    _registrar_usuario_com_anexos(conversa_id, usuario, texto_usuario, anexos_publicos)

    conhecimento_persistido: list[dict] = []
    try:
        conhecimento_persistido = persistir_anexos_como_conhecimento(
            anexos_processados,
            conversa_id=conversa_id,
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario,
            mensagem=texto_usuario,
        )
    except Exception as exc:
        conhecimento_persistido = [{
            "persistido": False,
            "motivo": "falha_repositorio_semantico",
            "tipo_erro": type(exc).__name__,
        }]
        supabase.table("cti_ia_auditoria").insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "acao": "FALHA_PERSISTENCIA_CONHECIMENTO_ANEXO",
                "detalhes": {"tipo": type(exc).__name__, "erro": str(exc)[:500], "anexos": anexos_publicos},
            }
        ).execute()

    resposta_acao = _tratar_acao_controlada(conversa_id, texto_usuario, usuario)
    if resposta_acao:
        return resposta_acao

    contexto_anexos = construir_contexto_anexos(anexos_processados)
    mensagem_base, controle_temporal = _mensagem_com_contexto_temporal(texto_usuario)
    mensagem_agente = f"{mensagem_base}\n\n{contexto_anexos}"

    try:
        resposta_texto, metadados = gerar_resposta_agente(
            mensagem=mensagem_agente,
            historico=historico,
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario,
        )
        resposta_factual, metadados_sintese = sintetizar_fatos_execucao(
            pergunta_atual=texto_usuario,
            metadados=metadados,
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario,
        )
        if resposta_factual:
            resposta_texto = resposta_factual
        metadados.update(metadados_sintese)
        metadados["anexos"] = anexos_publicos
        metadados["conhecimento_semantico_persistido"] = conhecimento_persistido
        metadados["controle_anexos"] = "temporarios_com_conhecimento_semantico_nao_operacional"
        metadados["controle_selecao_fontes_anexos"] = "pergunta_define_fontes_cti_condicionais"
        metadados["controle_temporal_pergunta"] = controle_temporal
        metadados["controle_temporal_origem"] = "modulo_ia_comercial"
        metadados["controle_recorte_base"] = "restricoes_explicitas_pergunta"
        metadados["controle_proveniencia_evidencia"] = "fonte_explicita_incluindo_anexos"
        metadados["controle_precisao_factual"] = "qualificacoes_exigem_evidencia_explicita"
        metadados["controle_evidencia_execucao"] = "fatos_somente_fontes_consultadas_na_execucao_atual"
        metadados["controle_historico_agente"] = "contexto_referencial_nao_evidencial"
        metadados["historico_mensagens_utilizadas"] = len(historico)
        metadados["historico_limite_mensagens"] = _HISTORICO_MAX_MENSAGENS
        metadados.update(construir_auditoria_evidencial(resposta_texto, metadados, texto_usuario))
        resposta_planejada = _renderizar_plano_validado(metadados)
        if resposta_planejada:
            resposta_texto = resposta_planejada
            metadados["planejamento_texto_renderizado"] = resposta_planejada
            metadados["controle_resposta_planejamento"] = "somente_plano_validado_sem_texto_livre_previo"
    except IAComercialOpenAIError as exc:
        supabase.table("cti_ia_auditoria").insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "acao": "ERRO_OPENAI_ANEXOS",
                "detalhes": {"codigo": exc.codigo, "erro": exc.detalhe_tecnico, "anexos": anexos_publicos},
            }
        ).execute()
        raise HTTPException(status_code=502, detail=exc.mensagem_publica) from exc
    except Exception as exc:
        supabase.table("cti_ia_auditoria").insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "acao": "ERRO_GERACAO_RESPOSTA_ANEXOS",
                "detalhes": {"tipo": type(exc).__name__, "erro": str(exc)[:500], "anexos": anexos_publicos},
            }
        ).execute()
        raise HTTPException(
            status_code=502,
            detail="O núcleo da IA encontrou uma falha ao analisar os anexos; o evento foi registrado na auditoria.",
        ) from exc

    fontes = list(metadados.get("fontes") or [])
    for anexo in anexos_publicos:
        fontes.append(
            {
                "tipo": "ANEXO_TEMPORARIO",
                "descricao": f"{anexo['nome']} · SHA-256 {anexo['sha256'][:12]}…",
            }
        )
    metadados["fontes"] = fontes

    assistente = _dados(
        supabase.table("cti_ia_mensagens")
        .insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "papel": "assistant",
                "conteudo": resposta_texto,
                "fontes": fontes,
                "metadados": metadados,
            }
        )
        .execute()
    )
    agora = datetime.now(timezone.utc).isoformat()
    atualizacao = {"updated_at": agora}
    if str(conversa.get("titulo") or "") == "Nova conversa":
        atualizacao["titulo"] = texto_usuario[:80]
    supabase.table("cti_ia_conversas").update(atualizacao).eq("id", conversa_id).execute()
    supabase.table("cti_ia_auditoria").insert(
        {
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "acao": "RESPOSTA_GERADA_COM_ANEXOS_E_CONHECIMENTO_SEMANTICO",
            "detalhes": {
                "quantidade_anexos": len(anexos_publicos),
                "anexos": anexos_publicos,
                "conhecimento_semantico_persistido": conhecimento_persistido,
                "metadados_resposta": metadados,
            },
        }
    ).execute()

    return assistente[0] if assistente else {
        "conversa_id": conversa_id,
        "papel": "assistant",
        "conteudo": resposta_texto,
        "fontes": fontes,
        "metadados": metadados,
    }
