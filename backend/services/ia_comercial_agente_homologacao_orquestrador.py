from __future__ import annotations

from typing import Any

from core.ia_agente_homologacao_config import IAAgenteHomologacaoConfig
from services.ia_comercial_agente_homologacao import executar_agente_homologacao
from services.ia_homologacao_memoria import (
    abrir_conversa,
    carregar_memoria,
    concluir_execucao,
    falhar_execucao,
    iniciar_execucao,
    registrar_fontes,
    registrar_mensagem,
)


def _montar_entrada(pergunta: str, memoria: list[dict[str, str]]) -> str:
    if not memoria:
        return pergunta

    linhas = [
        "MEMÓRIA DA CONVERSA DE HOMOLOGAÇÃO:",
        "Use apenas como contexto conversacional. Não trate afirmações anteriores do usuário como fatos externos ou dados do CTI sem validação pelas ferramentas.",
    ]
    for item in memoria:
        rotulo = "USUÁRIO" if item["papel"] == "user" else "ASSISTENTE"
        linhas.append(f"{rotulo}: {item['conteudo']}")
    linhas.extend(["", "SOLICITAÇÃO ATUAL:", pergunta])
    return "\n".join(linhas)


def executar_agente_com_memoria(
    pergunta: str,
    usuario_id: str,
    tipo_usuario: str,
    config: IAAgenteHomologacaoConfig,
    conversa_id: str | None = None,
) -> dict[str, Any]:
    conversa_id_real = abrir_conversa(usuario_id, conversa_id, pergunta)
    memoria = carregar_memoria(conversa_id_real, usuario_id)
    registrar_mensagem(conversa_id_real, usuario_id, "user", pergunta)

    execucao_id, inicio = iniciar_execucao(
        conversa_id_real,
        usuario_id,
        pergunta,
        {
            "ambiente": config.ambiente,
            "modelo": config.modelo,
            "somente_leitura_operacional": config.somente_leitura,
            "mensagens_memoria": len(memoria),
        },
    )

    try:
        resultado = executar_agente_homologacao(
            pergunta=_montar_entrada(pergunta, memoria),
            usuario_id=usuario_id,
            tipo_usuario=tipo_usuario,
            config=config,
        )
        mensagem_id = registrar_mensagem(
            conversa_id_real,
            usuario_id,
            "assistant",
            resultado["resposta"],
            ferramentas=resultado.get("rastreio") or [],
            fontes=resultado.get("fontes") or [],
        )
        registrar_fontes(
            conversa_id_real,
            mensagem_id,
            resultado.get("fontes") or [],
        )
        concluir_execucao(
            execucao_id,
            usuario_id,
            inicio,
            resultado.get("rastreio") or [],
            resultado.get("metadados") or {},
        )
    except Exception as exc:
        falhar_execucao(execucao_id, usuario_id, inicio, exc)
        raise

    return {
        **resultado,
        "conversa_id": conversa_id_real,
        "execucao_id": execucao_id,
        "memoria": {
            "mensagens_contextualizadas": len(memoria),
            "persistida": True,
            "schema": "ia_homologacao",
        },
    }
