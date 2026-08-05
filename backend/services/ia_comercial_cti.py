from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from core.supabase_client import supabase
from services.ia_comercial_historico import contexto_historico

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
WEB_MODEL = os.getenv("OPENAI_WEB_MODEL", "gpt-4o-mini-search-preview")
MAX_CONTEXT_ROWS = 120

SYSTEM_PROMPT = """Você é a IA Comercial CTI, assistente geral e exclusivo da operação Viena SP / Carrier.
Compreenda o CTI como um sistema único: base histórica CTI/ANFIR, Dashboard Executivo, CRM, clientes,
oportunidades, pipeline, propostas, pedidos, atividades, produtos, territórios, usuários e documentos.
Responda em português do Brasil, de forma objetiva, prática e auditável.
Escolha autonomamente entre dados internos, pesquisa web ou cruzamento das duas fontes.
Nunca invente clientes, valores, datas, vendas, pedidos ou fatos externos.
Diferencie claramente: fatos do CTI, fatos da web e inferências.
As permissões limitam somente os dados e ações disponíveis ao usuário; não limitam seu raciocínio.
Nesta fase, você consulta e analisa, mas não altera registros.
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
    oportunidades = _consulta_segura("cti_oportunidades")
    propostas = _consulta_segura("cti_propostas")
    pedidos = _consulta_segura("cti_pedidos")
    clientes = _consulta_segura("clientes") or _consulta_segura("cti_clientes")
    atividades = _consulta_segura("cti_atividades")
    itens = _consulta_segura("cti_oportunidade_itens")

    if tipo_usuario != "ADMIN_MASTER":
        oportunidades = [item for item in oportunidades if str(item.get("responsavel_id") or "") == usuario_id]
        oportunidade_ids = {str(item.get("id")) for item in oportunidades if item.get("id")}
        propostas = [item for item in propostas if str(item.get("oportunidade_id") or "") in oportunidade_ids]
        pedidos = [item for item in pedidos if str(item.get("oportunidade_id") or "") in oportunidade_ids]
        atividades = [item for item in atividades if str(item.get("responsavel_id") or item.get("usuario_id") or "") == usuario_id]
        itens = [item for item in itens if str(item.get("oportunidade_id") or "") in oportunidade_ids]
        cliente_ids = {str(item.get("cliente_id")) for item in oportunidades if item.get("cliente_id")}
        clientes = [item for item in clientes if str(item.get("id") or "") in cliente_ids]

    historico = contexto_historico(tipo_usuario)
    return {
        "escopo": "global" if tipo_usuario == "ADMIN_MASTER" else "usuario_autorizado",
        "fontes_disponiveis": [
            "Base histórica CTI/ANFIR e Dashboard Executivo",
            "Clientes e cadastros autorizados",
            "Oportunidades, itens, pipeline, propostas e pedidos",
            "Atividades e histórico operacional",
            "Pesquisa web quando necessária",
        ],
        "quantidades": {
            "clientes_crm": len(clientes),
            "oportunidades": len(oportunidades),
            "itens": len(itens),
            "propostas": len(propostas),
            "pedidos": len(pedidos),
            "atividades": len(atividades),
            "registros_historicos": historico.get("dashboard_historico", {}).get("total_registros", 0),
        },
        "crm": {
            "clientes": clientes,
            "oportunidades": oportunidades,
            "itens": itens,
            "propostas": propostas,
            "pedidos": pedidos,
            "atividades": atividades,
        },
        "historico_dashboard": historico,
    }


def _classificar_falha_openai(exc: Exception) -> IAComercialOpenAIError:
    status_code = getattr(exc, "status_code", None)
    corpo = str(exc)
    normalizado = corpo.lower()
    tipo = type(exc).__name__
    detalhe = f"{tipo}; status={status_code}; {corpo}"
    if status_code == 401 or "invalid_api_key" in normalizado:
        return IAComercialOpenAIError("A chave OpenAI configurada foi rejeitada.", codigo="OPENAI_AUTH", detalhe_tecnico=detalhe)
    if status_code == 429 or "quota" in normalizado:
        return IAComercialOpenAIError("A conta OpenAI atingiu o saldo ou limite de uso.", codigo="OPENAI_QUOTA", detalhe_tecnico=detalhe)
    if status_code == 404 or "model_not_found" in normalizado:
        return IAComercialOpenAIError("O modelo OpenAI configurado não está disponível.", codigo="OPENAI_MODEL", detalhe_tecnico=detalhe)
    if "connection" in tipo.lower() or "timeout" in tipo.lower():
        return IAComercialOpenAIError("O backend não conseguiu se comunicar com a OpenAI.", codigo="OPENAI_CONNECTION", detalhe_tecnico=detalhe)
    return IAComercialOpenAIError("A OpenAI não concluiu a resposta.", codigo="OPENAI_UNKNOWN", detalhe_tecnico=detalhe)


def _decidir_fontes(client: OpenAI, mensagem: str, historico: list[dict[str, str]]) -> str:
    instrucao = (
        "Classifique a fonte necessária para responder à última pergunta. "
        "Responda somente INTERNO, WEB ou HIBRIDO. "
        "INTERNO: dados do CTI. WEB: informação externa atual. HIBRIDO: cruzamento dos dois."
    )
    try:
        resposta = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": instrucao}, *historico[-6:], {"role": "user", "content": mensagem}],
            temperature=0,
            max_tokens=8,
        )
        texto = str(resposta.choices[0].message.content or "INTERNO").strip().upper()
        return texto if texto in {"INTERNO", "WEB", "HIBRIDO"} else "INTERNO"
    except Exception:
        return "INTERNO"


def _fontes_web(mensagem_objeto: Any) -> list[dict[str, str]]:
    fontes: list[dict[str, str]] = []
    for anotacao in getattr(mensagem_objeto, "annotations", None) or []:
        url = getattr(anotacao, "url", None)
        titulo = getattr(anotacao, "title", None)
        citacao = getattr(anotacao, "url_citation", None)
        if citacao:
            url = url or getattr(citacao, "url", None)
            titulo = titulo or getattr(citacao, "title", None)
        if url and not any(item.get("url") == url for item in fontes):
            fontes.append({"tipo": "WEB", "descricao": str(titulo or url), "url": str(url)})
    return fontes


def gerar_resposta(mensagem: str, historico: list[dict[str, str]], contexto: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise IAComercialOpenAIError("OPENAI_API_KEY não está configurada no backend.", codigo="OPENAI_KEY_MISSING")

    client = OpenAI(api_key=api_key, timeout=90.0, max_retries=1)
    modo = _decidir_fontes(client, mensagem, historico)
    entradas: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "Contexto interno autorizado do CTI em JSON:\n" + json.dumps(contexto, ensure_ascii=False, default=str)},
        *historico[-20:],
        {"role": "user", "content": mensagem},
    ]

    modelo_usado = WEB_MODEL if modo in {"WEB", "HIBRIDO"} else MODEL
    try:
        resposta = client.chat.completions.create(model=modelo_usado, messages=entradas, temperature=0.2)
    except Exception as exc:
        raise _classificar_falha_openai(exc) from exc

    escolha = resposta.choices[0] if getattr(resposta, "choices", None) else None
    mensagem_resposta = getattr(escolha, "message", None)
    texto = str(getattr(mensagem_resposta, "content", "") or "").strip()
    if not texto:
        raise IAComercialOpenAIError("O modelo respondeu sem conteúdo textual.", codigo="OPENAI_EMPTY_RESPONSE")

    fontes = [{"tipo": "CTI", "descricao": "Sistema CTI completo e base histórica do Dashboard Executivo."}]
    if modo == "WEB":
        fontes = []
    if modo in {"WEB", "HIBRIDO"}:
        fontes.extend(_fontes_web(mensagem_resposta))
        if not any(item.get("tipo") == "WEB" for item in fontes):
            fontes.append({"tipo": "WEB", "descricao": "Pesquisa web executada pelo modelo de busca OpenAI."})

    uso = getattr(resposta, "usage", None)
    metadados = {
        "modelo": modelo_usado,
        "modo_fontes": modo,
        "fontes": fontes,
        "response_id": getattr(resposta, "id", None),
        "escopo": contexto.get("escopo"),
        "quantidades_contexto": contexto.get("quantidades", {}),
        "tokens_entrada": getattr(uso, "prompt_tokens", None),
        "tokens_saida": getattr(uso, "completion_tokens", None),
    }
    return texto, metadados
