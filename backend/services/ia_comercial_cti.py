from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from core.supabase_client import supabase

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
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


def gerar_resposta(mensagem: str, historico: list[dict[str, str]], contexto: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada no backend.")

    entradas: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": "Contexto CTI atual em JSON:\n" + json.dumps(contexto, ensure_ascii=False, default=str),
        },
    ]
    entradas.extend(historico[-20:])
    entradas.append({"role": "user", "content": mensagem})

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(model=MODEL, input=entradas)
    texto = (getattr(resposta, "output_text", None) or "").strip()
    if not texto:
        texto = "Não foi possível gerar uma resposta textual nesta execução."

    metadados = {
        "modelo": MODEL,
        "response_id": getattr(resposta, "id", None),
        "escopo": contexto.get("escopo"),
        "quantidades_contexto": contexto.get("quantidades", {}),
    }
    return texto, metadados
