from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from core.supabase_client import supabase
from services.ia_comercial_historico import contexto_historico

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
WEB_MODEL = os.getenv("OPENAI_WEB_MODEL", "gpt-4.1-mini")
MAX_CONTEXT_ROWS = 120
CONTEXT_PAGE_SIZE = 1000

STATUS_OPORTUNIDADE_ENCERRADA = {
    "GANHO",
    "PERDIDO",
    "CANCELADO",
    "CANCELADA",
    "CONCLUIDO",
    "CONCLUÍDO",
    "ENCERRADO",
}
STATUS_PEDIDO_ENCERRADO = {
    "ENCERRADO",
    "CANCELADO",
    "CANCELADA",
    "CONCLUIDO",
    "CONCLUÍDO",
}

SYSTEM_PROMPT = """Você é a IA Comercial CTI, assistente geral e exclusivo da operação Viena SP / Carrier.
Compreenda o CTI como um sistema único: base histórica CTI/ANFIR, Dashboard Executivo, CRM, clientes,
oportunidades, pipeline, propostas, pedidos, atividades, produtos, territórios, usuários e documentos.
Responda em português do Brasil, de forma objetiva, prática e auditável.
Escolha autonomamente entre dados internos, pesquisa web ou cruzamento das duas fontes.
Nunca invente clientes, valores, datas, vendas, pedidos ou fatos externos.
Diferencie claramente: fatos do CTI, fatos da web e inferências.
As permissões limitam somente os dados e ações disponíveis ao usuário; não limitam seu raciocínio.
Nesta fase, você consulta e analisa, mas não altera registros.
Quando usar a web, execute a pesquisa de fato, cite as fontes encontradas e nunca diga ao usuário para pesquisar manualmente.
Os campos de quantidades e valores consolidados do contexto interno são calculados sobre o conjunto completo autorizado.
Os arrays detalhados em crm podem ser amostras limitadas para controle de contexto. Em perguntas quantitativas,
use os consolidados; não derive totais contando a amostra e não apresente uma amostra como lista exaustiva.
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


def _consulta_segura(tabela: str, colunas: str = "*") -> list[dict[str, Any]]:
    """Lê integralmente uma fonte interna, paginando para não truncar métricas da IA."""
    registros: list[dict[str, Any]] = []
    inicio = 0
    try:
        while True:
            lote = _dados(
                supabase.table(tabela)
                .select(colunas)
                .range(inicio, inicio + CONTEXT_PAGE_SIZE - 1)
                .execute()
            )
            registros.extend(lote)
            if len(lote) < CONTEXT_PAGE_SIZE:
                break
            inicio += CONTEXT_PAGE_SIZE
        return registros
    except Exception:
        return []


def _status(valor: Any) -> str:
    return str(valor or "").strip().upper().replace(" ", "_")


def _numero(valor: Any) -> float:
    if valor in (None, ""):
        return 0.0
    try:
        if isinstance(valor, str):
            texto = valor.strip().replace("R$", "").replace(" ", "")
            if "," in texto:
                texto = texto.replace(".", "").replace(",", ".")
            return float(texto)
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _oportunidade_aberta(item: dict[str, Any]) -> bool:
    return _status(item.get("status")) not in STATUS_OPORTUNIDADE_ENCERRADA


def _pedido_em_curso(item: dict[str, Any]) -> bool:
    return _status(item.get("status")) not in STATUS_PEDIDO_ENCERRADO


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

    oportunidades_abertas = [item for item in oportunidades if _oportunidade_aberta(item)]
    pedidos_em_curso = [item for item in pedidos if _pedido_em_curso(item)]
    valor_pedidos_em_curso = round(
        sum(_numero(item.get("valor") if item.get("valor") is not None else item.get("valor_total")) for item in pedidos_em_curso),
        2,
    )

    historico = contexto_historico(tipo_usuario)
    quantidades = {
        "clientes_crm": len(clientes),
        "oportunidades": len(oportunidades),
        "oportunidades_abertas": len(oportunidades_abertas),
        "itens": len(itens),
        "propostas": len(propostas),
        "pedidos": len(pedidos),
        "pedidos_em_curso": len(pedidos_em_curso),
        "atividades": len(atividades),
        "registros_historicos": historico.get("dashboard_historico", {}).get("total_registros", 0),
    }
    return {
        "escopo": "global" if tipo_usuario == "ADMIN_MASTER" else "usuario_autorizado",
        "fontes_disponiveis": [
            "Base histórica CTI/ANFIR e Dashboard Executivo",
            "Clientes e cadastros autorizados",
            "Oportunidades, itens, pipeline, propostas e pedidos",
            "Atividades e histórico operacional",
            "Pesquisa web quando necessária",
        ],
        "quantidades": quantidades,
        "valores": {
            "pedidos_em_curso": valor_pedidos_em_curso,
        },
        "amostragem_detalhes": {
            "limite_por_fonte": MAX_CONTEXT_ROWS,
            "totais_calculados_sobre_base_completa": True,
        },
        "crm": {
            "clientes": clientes[:MAX_CONTEXT_ROWS],
            "oportunidades": oportunidades[:MAX_CONTEXT_ROWS],
            "itens": itens[:MAX_CONTEXT_ROWS],
            "propostas": propostas[:MAX_CONTEXT_ROWS],
            "pedidos": pedidos[:MAX_CONTEXT_ROWS],
            "atividades": atividades[:MAX_CONTEXT_ROWS],
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
    if status_code in {400, 422}:
        return IAComercialOpenAIError("A solicitação da IA foi recusada por incompatibilidade técnica.", codigo="OPENAI_REQUEST", detalhe_tecnico=detalhe)
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


def _fonte_unica(fontes: list[dict[str, str]], descricao: str, url: str) -> None:
    if url and not any(item.get("url") == url for item in fontes):
        fontes.append({"tipo": "WEB", "descricao": descricao or url, "url": url})


def _fontes_responses(resposta: Any) -> list[dict[str, str]]:
    fontes: list[dict[str, str]] = []
    for item in getattr(resposta, "output", None) or []:
        if getattr(item, "type", None) == "web_search_call":
            acao = getattr(item, "action", None)
            for origem in getattr(acao, "sources", None) or []:
                _fonte_unica(fontes, str(getattr(origem, "title", "") or ""), str(getattr(origem, "url", "") or ""))
        if getattr(item, "type", None) != "message":
            continue
        for parte in getattr(item, "content", None) or []:
            for anotacao in getattr(parte, "annotations", None) or []:
                citacao = getattr(anotacao, "url_citation", None) or anotacao
                _fonte_unica(
                    fontes,
                    str(getattr(citacao, "title", "") or ""),
                    str(getattr(citacao, "url", "") or ""),
                )
    return fontes


def _responder_com_web(
    client: OpenAI,
    mensagem: str,
    historico: list[dict[str, str]],
    contexto: dict[str, Any],
) -> tuple[str, Any, list[dict[str, str]]]:
    entrada = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": "Contexto interno autorizado do CTI em JSON:\n" + json.dumps(contexto, ensure_ascii=False, default=str),
        },
        *historico[-20:],
        {"role": "user", "content": mensagem},
    ]
    resposta = client.responses.create(
        model=WEB_MODEL,
        tools=[{
            "type": "web_search_preview",
            "search_context_size": "medium",
            "user_location": {
                "type": "approximate",
                "country": "BR",
                "region": "São Paulo",
                "city": "São Paulo",
                "timezone": "America/Sao_Paulo",
            },
        }],
        tool_choice="required",
        input=entrada,
        store=False,
    )
    texto = str(getattr(resposta, "output_text", "") or "").strip()
    return texto, resposta, _fontes_responses(resposta)


def _responder_interno(
    client: OpenAI,
    mensagem: str,
    historico: list[dict[str, str]],
    contexto: dict[str, Any],
) -> tuple[str, Any]:
    entradas: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": "Contexto interno autorizado do CTI em JSON:\n" + json.dumps(contexto, ensure_ascii=False, default=str),
        },
        *historico[-20:],
        {"role": "user", "content": mensagem},
    ]
    resposta = client.chat.completions.create(model=MODEL, messages=entradas, temperature=0.2)
    escolha = resposta.choices[0] if getattr(resposta, "choices", None) else None
    texto = str(getattr(getattr(escolha, "message", None), "content", "") or "").strip()
    return texto, resposta


def gerar_resposta(mensagem: str, historico: list[dict[str, str]], contexto: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise IAComercialOpenAIError("OPENAI_API_KEY não está configurada no backend.", codigo="OPENAI_KEY_MISSING")

    client = OpenAI(api_key=api_key, timeout=90.0, max_retries=1)
    modo = _decidir_fontes(client, mensagem, historico)
    fontes: list[dict[str, str]] = []
    modelo_usado = MODEL

    try:
        if modo in {"WEB", "HIBRIDO"}:
            modelo_usado = WEB_MODEL
            texto, resposta, fontes_web = _responder_com_web(client, mensagem, historico, contexto)
            fontes.extend(fontes_web)
            if modo == "HIBRIDO":
                fontes.insert(0, {"tipo": "CTI", "descricao": "Sistema CTI completo e base histórica do Dashboard Executivo."})
        else:
            texto, resposta = _responder_interno(client, mensagem, historico, contexto)
            fontes = [{"tipo": "CTI", "descricao": "Sistema CTI completo e base histórica do Dashboard Executivo."}]
    except Exception as exc:
        raise _classificar_falha_openai(exc) from exc

    if not texto:
        raise IAComercialOpenAIError("O modelo respondeu sem conteúdo textual.", codigo="OPENAI_EMPTY_RESPONSE")
    if modo in {"WEB", "HIBRIDO"} and not any(item.get("tipo") == "WEB" and item.get("url") for item in fontes):
        raise IAComercialOpenAIError(
            "A pesquisa web não retornou fontes verificáveis nesta execução.",
            codigo="OPENAI_WEB_WITHOUT_SOURCES",
        )

    uso = getattr(resposta, "usage", None)
    metadados = {
        "modelo": modelo_usado,
        "modo_fontes": modo,
        "pesquisa_web_executada": modo in {"WEB", "HIBRIDO"},
        "fontes": fontes,
        "response_id": getattr(resposta, "id", None),
        "escopo": contexto.get("escopo"),
        "quantidades_contexto": contexto.get("quantidades", {}),
        "tokens_entrada": getattr(uso, "input_tokens", None) or getattr(uso, "prompt_tokens", None),
        "tokens_saida": getattr(uso, "output_tokens", None) or getattr(uso, "completion_tokens", None),
    }
    return texto, metadados
