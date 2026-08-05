from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from core.ia_agente_homologacao_config import IAAgenteHomologacaoConfig
from services.ia_comercial_cti import contexto_comercial
from services.ia_comercial_historico import contexto_historico

MAX_ITERACOES = 6

INSTRUCOES = """Você é o agente experimental da IA Comercial CTI, em ambiente isolado de homologação.
Compreenda a solicitação livremente e escolha autonomamente as ferramentas necessárias.
Use as ferramentas internas para fatos do CTI e a pesquisa web para fatos externos, atuais ou verificáveis.
Quando o usuário pedir pesquisa, notícias, mercado, concorrentes, legislação, tendências, dados atuais ou fontes,
execute pesquisa web real. Não substitua pesquisa por conhecimento geral.
Cruze CTI e web quando isso melhorar a resposta. Diferencie fatos internos, fatos externos e inferências.
Nunca invente números, clientes, compras, oportunidades, datas, notícias ou fontes.
Cite fontes web identificáveis. Informe também quais consultas internas foram executadas.
Você está estritamente em modo somente leitura: não proponha nem tente executar alteração de dados.
Responda em português do Brasil, com profundidade proporcional à pergunta e linguagem comercial clara.
"""


def _dados_dominio(usuario_id: str, tipo_usuario: str, dominio: str) -> Any:
    contexto = contexto_comercial(usuario_id, tipo_usuario)
    if dominio == "resumo":
        return {
            "escopo": contexto.get("escopo"),
            "quantidades": contexto.get("quantidades"),
            "fontes_disponiveis": contexto.get("fontes_disponiveis"),
        }
    return contexto.get("crm", {}).get(dominio, [])


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _filtrar_registros(registros: list[dict[str, Any]], termo: str | None, limite: int) -> list[dict[str, Any]]:
    limite = max(1, min(int(limite or 30), 80))
    if not termo:
        return registros[:limite]
    alvo = _normalizar(termo)
    resultado = [
        item for item in registros
        if alvo in _normalizar(json.dumps(item, ensure_ascii=False, default=str))
    ]
    return resultado[:limite]


def _executar_ferramenta(
    nome: str,
    argumentos: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
) -> dict[str, Any]:
    if nome == "consultar_resumo_cti":
        return {"ferramenta": nome, "resultado": _dados_dominio(usuario_id, tipo_usuario, "resumo")}

    if nome == "consultar_dominio_crm":
        dominio = str(argumentos.get("dominio") or "oportunidades")
        permitidos = {"clientes", "oportunidades", "itens", "propostas", "pedidos", "atividades"}
        if dominio not in permitidos:
            return {"ferramenta": nome, "erro": "Domínio não permitido em homologação."}
        registros = _dados_dominio(usuario_id, tipo_usuario, dominio)
        if not isinstance(registros, list):
            registros = []
        filtrados = _filtrar_registros(
            registros,
            str(argumentos.get("termo") or "") or None,
            int(argumentos.get("limite") or 30),
        )
        return {
            "ferramenta": nome,
            "dominio": dominio,
            "total_disponivel_no_contexto": len(registros),
            "total_retornado": len(filtrados),
            "resultado": filtrados,
        }

    if nome == "consultar_historico_dashboard":
        historico = contexto_historico(tipo_usuario)
        termo = str(argumentos.get("termo") or "") or None
        limite = int(argumentos.get("limite") or 40)
        registros = historico.get("registros_ultimos_90_dias", [])
        if not isinstance(registros, list):
            registros = []
        return {
            "ferramenta": nome,
            "fonte": historico.get("fonte"),
            "escopo": historico.get("escopo"),
            "dashboard_historico": historico.get("dashboard_historico"),
            "periodo_recente": historico.get("periodo_recente"),
            "registros_filtrados": _filtrar_registros(registros, termo, limite),
            "observacao_amostragem": historico.get("observacao_amostragem"),
        }

    return {"ferramenta": nome, "erro": "Ferramenta desconhecida ou não autorizada."}


def _ferramentas() -> list[dict[str, Any]]:
    return [
        {
            "type": "web_search",
            "search_context_size": "high",
            "user_location": {
                "type": "approximate",
                "country": "BR",
                "region": "São Paulo",
                "city": "São Paulo",
                "timezone": "America/Sao_Paulo",
            },
        },
        {
            "type": "function",
            "name": "consultar_resumo_cti",
            "description": "Consulta quantidades e escopo geral autorizado do CTI, sem alterar dados.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            "strict": True,
        },
        {
            "type": "function",
            "name": "consultar_dominio_crm",
            "description": "Consulta registros autorizados de um domínio operacional do CRM do CTI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dominio": {
                        "type": "string",
                        "enum": ["clientes", "oportunidades", "itens", "propostas", "pedidos", "atividades"],
                    },
                    "termo": {"type": ["string", "null"]},
                    "limite": {"type": "integer", "minimum": 1, "maximum": 80},
                },
                "required": ["dominio", "termo", "limite"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "consultar_historico_dashboard",
            "description": "Consulta a base histórica CTI/ANFIR e os indicadores usados pelo Dashboard Executivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {"type": ["string", "null"]},
                    "limite": {"type": "integer", "minimum": 1, "maximum": 80},
                },
                "required": ["termo", "limite"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]


def _fontes_web(resposta: Any) -> list[dict[str, str]]:
    fontes: list[dict[str, str]] = []
    for item in getattr(resposta, "output", None) or []:
        if getattr(item, "type", None) == "web_search_call":
            acao = getattr(item, "action", None)
            for origem in getattr(acao, "sources", None) or []:
                url = str(getattr(origem, "url", "") or "")
                titulo = str(getattr(origem, "title", "") or url)
                if url and not any(fonte.get("url") == url for fonte in fontes):
                    fontes.append({"tipo": "WEB", "descricao": titulo, "url": url})
        if getattr(item, "type", None) != "message":
            continue
        for parte in getattr(item, "content", None) or []:
            for anotacao in getattr(parte, "annotations", None) or []:
                citacao = getattr(anotacao, "url_citation", None) or anotacao
                url = str(getattr(citacao, "url", "") or "")
                titulo = str(getattr(citacao, "title", "") or url)
                if url and not any(fonte.get("url") == url for fonte in fontes):
                    fontes.append({"tipo": "WEB", "descricao": titulo, "url": url})
    return fontes


def executar_agente_homologacao(
    pergunta: str,
    usuario_id: str,
    tipo_usuario: str,
    config: IAAgenteHomologacaoConfig,
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada no ambiente de homologação.")

    client = OpenAI(api_key=api_key, timeout=120.0, max_retries=1)
    ferramentas = _ferramentas()
    rastreio: list[dict[str, Any]] = []

    resposta = client.responses.create(
        model=config.modelo,
        instructions=INSTRUCOES,
        input=pergunta,
        tools=ferramentas,
        store=False,
    )

    for _ in range(MAX_ITERACOES):
        chamadas = [
            item for item in (getattr(resposta, "output", None) or [])
            if getattr(item, "type", None) == "function_call"
        ]
        if not chamadas:
            break

        saidas = []
        for chamada in chamadas:
            try:
                argumentos = json.loads(str(getattr(chamada, "arguments", "{}") or "{}"))
            except json.JSONDecodeError:
                argumentos = {}
            resultado = _executar_ferramenta(
                str(getattr(chamada, "name", "")),
                argumentos,
                usuario_id,
                tipo_usuario,
            )
            rastreio.append({
                "tipo": "CTI",
                "ferramenta": getattr(chamada, "name", ""),
                "argumentos": argumentos,
                "resumo": {
                    "dominio": resultado.get("dominio"),
                    "total_retornado": resultado.get("total_retornado"),
                    "erro": resultado.get("erro"),
                },
            })
            saidas.append({
                "type": "function_call_output",
                "call_id": getattr(chamada, "call_id", ""),
                "output": json.dumps(resultado, ensure_ascii=False, default=str),
            })

        resposta = client.responses.create(
            model=config.modelo,
            instructions=INSTRUCOES,
            previous_response_id=getattr(resposta, "id", None),
            input=saidas,
            tools=ferramentas,
            store=False,
        )

    texto = str(getattr(resposta, "output_text", "") or "").strip()
    if not texto:
        raise RuntimeError("O agente experimental não produziu resposta textual.")

    fontes = _fontes_web(resposta)
    if fontes:
        rastreio.append({"tipo": "WEB", "fontes_encontradas": len(fontes)})

    uso = getattr(resposta, "usage", None)
    return {
        "resposta": texto,
        "fontes": fontes,
        "rastreio": rastreio,
        "metadados": {
            "ambiente": config.ambiente,
            "somente_leitura": config.somente_leitura,
            "modelo": config.modelo,
            "response_id": getattr(resposta, "id", None),
            "tokens_entrada": getattr(uso, "input_tokens", None),
            "tokens_saida": getattr(uso, "output_tokens", None),
            "iteracoes_maximas": MAX_ITERACOES,
        },
    }
