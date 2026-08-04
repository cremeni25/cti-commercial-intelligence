from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from core.supabase_client import supabase

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_CONTEXT_ROWS = 80

SYSTEM_PROMPT = """Você é a IA Comercial CTI, assistente exclusivo da operação comercial Viena SP / Carrier.
Responda em português do Brasil, de forma objetiva, prática e auditável.
Use somente os dados CTI fornecidos no contexto e conhecimento geral seguro.
Nunca invente clientes, valores, propostas, pedidos, datas ou probabilidades.
Diferencie claramente fatos do CTI, análise e hipótese.
Nesta fase você possui acesso somente de leitura e não altera registros.
Respeite o perfil do usuário e não revele dados fora do contexto autorizado.
Quando os dados forem insuficientes, diga exatamente o que falta.
"""


class IAComercialOpenAIError(RuntimeError):
    def __init__(self, mensagem_publica: str, *, codigo: str, detalhe_tecnico: str = ""):
        super().__init__(mensagem_publica)
        self.mensagem_publica = mensagem_publica
        self.codigo = codigo
        self.detalhe_tecnico = detalhe_tecnico[:500]


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _consulta_segura(tabela: str, colunas: str = "*", limite: int = MAX_CONTEXT_ROWS) -> list[dict[str, Any]]:
    try:
        return _dados(supabase.table(tabela).select(colunas).limit(limite).execute())
    except Exception:
        return []


def contexto_comercial(usuario_id: str, tipo_usuario: str) -> dict[str, Any]:
    oportunidades = _consulta_segura(
        "cti_oportunidades",
        "id,cliente_id,responsavel_id,titulo,descricao,status,valor_estimado,probabilidade,data_fechamento_prevista,created_at",
    )
    propostas = _consulta_segura(
        "cti_propostas",
        "id,oportunidade_id,cliente_id,numero,status,valor_total,created_at",
    )
    pedidos = _consulta_segura(
        "cti_pedidos",
        "id,oportunidade_id,proposta_id,cliente_id,numero,status,valor_total,created_at",
    )
    clientes = _consulta_segura("clientes", "id,nome,cidade,estado,segmento,ddd,sub_regiao")

    if tipo_usuario != "ADMIN_MASTER":
        oportunidades = [
            item for item in oportunidades
            if str(item.get("responsavel_id") or "") == usuario_id
        ]
        oportunidade_ids = {str(item.get("id")) for item in oportunidades if item.get("id")}
        propostas = [item for item in propostas if str(item.get("oportunidade_id") or "") in oportunidade_ids]
        pedidos = [item for item in pedidos if str(item.get("oportunidade_id") or "") in oportunidade_ids]
        cliente_ids = {str(item.get("cliente_id")) for item in oportunidades if item.get("cliente_id")}
        clientes = [item for item in clientes if str(item.get("id") or "") in cliente_ids]

    return {
        "escopo": "global" if tipo_usuario == "ADMIN_MASTER" else "proprio_usuario",
        "quantidades": {
            "clientes": len(clientes),
            "oportunidades": len(oportunidades),
            "propostas": len(propostas),
            "pedidos": len(pedidos),
        },
        "clientes": clientes,
        "oportunidades": oportunidades,
        "propostas": propostas,
        "pedidos": pedidos,
    }


def _classificar_falha_openai(exc: Exception) -> IAComercialOpenAIError:
    status_code = getattr(exc, "status_code", None)
    corpo = str(exc)
    corpo_normalizado = corpo.lower()
    codigo_api = str(getattr(exc, "code", "") or "").lower()
    tipo = type(exc).__name__
    detalhe = f"{tipo}; status={status_code}; code={codigo_api}; {corpo}"

    if status_code == 401 or "invalid_api_key" in corpo_normalizado or "authentication" in tipo.lower():
        return IAComercialOpenAIError(
            "A chave OpenAI configurada no backend foi rejeitada. Verifique a chave exclusiva da IA Comercial CTI no Render.",
            codigo="OPENAI_AUTH",
            detalhe_tecnico=detalhe,
        )
    if status_code == 429 or "insufficient_quota" in corpo_normalizado or "quota" in corpo_normalizado:
        return IAComercialOpenAIError(
            "A conta OpenAI do projeto está sem saldo disponível ou atingiu o limite de uso. Verifique faturamento e limites do projeto IA Comercial CTI.",
            codigo="OPENAI_QUOTA",
            detalhe_tecnico=detalhe,
        )
    if status_code == 404 or "model_not_found" in corpo_normalizado:
        return IAComercialOpenAIError(
            f"O modelo OpenAI configurado ({MODEL}) não está disponível para este projeto.",
            codigo="OPENAI_MODEL",
            detalhe_tecnico=detalhe,
        )
    if status_code in {400, 422}:
        return IAComercialOpenAIError(
            "A solicitação enviada ao modelo foi recusada por incompatibilidade técnica e precisa de ajuste no backend.",
            codigo="OPENAI_REQUEST",
            detalhe_tecnico=detalhe,
        )
    if "connection" in tipo.lower() or "timeout" in tipo.lower():
        return IAComercialOpenAIError(
            "O backend não conseguiu se comunicar com a OpenAI nesta tentativa.",
            codigo="OPENAI_CONNECTION",
            detalhe_tecnico=detalhe,
        )
    return IAComercialOpenAIError(
        "A OpenAI não concluiu a resposta. A ocorrência foi registrada na auditoria técnica da IA Comercial CTI.",
        codigo="OPENAI_UNKNOWN",
        detalhe_tecnico=detalhe,
    )


def gerar_resposta(mensagem: str, historico: list[dict[str, str]], contexto: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise IAComercialOpenAIError(
            "OPENAI_API_KEY não está configurada no backend.",
            codigo="OPENAI_KEY_MISSING",
        )

    entradas: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": "Contexto CTI atual em JSON:\n" + json.dumps(contexto, ensure_ascii=False, default=str),
        },
    ]
    entradas.extend(historico[-20:])
    entradas.append({"role": "user", "content": mensagem})

    client = OpenAI(api_key=api_key, timeout=60.0, max_retries=1)
    try:
        resposta = client.chat.completions.create(
            model=MODEL,
            messages=entradas,
            temperature=0.2,
        )
    except Exception as exc:
        raise _classificar_falha_openai(exc) from exc

    escolha = resposta.choices[0] if getattr(resposta, "choices", None) else None
    texto = str(getattr(getattr(escolha, "message", None), "content", "") or "").strip()
    if not texto:
        raise IAComercialOpenAIError(
            "O modelo respondeu sem conteúdo textual.",
            codigo="OPENAI_EMPTY_RESPONSE",
        )

    uso = getattr(resposta, "usage", None)
    metadados = {
        "modelo": MODEL,
        "response_id": getattr(resposta, "id", None),
        "escopo": contexto.get("escopo"),
        "quantidades_contexto": contexto.get("quantidades", {}),
        "tokens_entrada": getattr(uso, "prompt_tokens", None),
        "tokens_saida": getattr(uso, "completion_tokens", None),
    }
    return texto, metadados
