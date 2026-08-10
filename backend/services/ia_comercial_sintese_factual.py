from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from services.ia_comercial_agente import _executar_ferramenta_cti
from services.ia_comercial_cti import IAComercialOpenAIError, _classificar_falha_openai


SYNTHESIS_MODEL = os.getenv("OPENAI_AGENT_MODEL", os.getenv("OPENAI_WEB_MODEL", "gpt-4.1-mini"))

DOMINIOS_FACTUAIS = {
    "cti_atual",
    "historico",
    "anfir",
    "territorio",
    "produtos",
    "vendas",
    "clientes",
    "oportunidades",
    "relacionamentos_vendas",
}

INSTRUCOES_SINTESE_FATUAL = """Você é a camada de síntese factual da IA Comercial CTI.
Sua única função é responder à PERGUNTA_ATUAL usando exclusivamente as EVIDENCIAS_EXECUCAO fornecidas no JSON de entrada.
Você não recebe histórico de conversa, resposta preliminar do agente nem conhecimento operacional implícito como evidência.

REGRAS ABSOLUTAS DE EVIDÊNCIA:
- Não invente, complete ou reutilize fatos ausentes das EVIDENCIAS_EXECUCAO.
- DOMINIOS_NAO_CONSULTADOS são explicitamente desconhecidos nesta execução. Não faça afirmações positivas nem negativas sobre eles.
- Se oportunidades não foram consultadas, não diga que existem, não existem, estão abertas, fechadas, ganhas, perdidas ou ausentes do pipeline.
- Se vendas não foram consultadas, não diga que existem ou não existem vendas, nem ausência de vínculo de venda.
- Se produtos não foram consultados, não nomeie modelos do catálogo, portfólio atual ou disponibilidade comercial. Modelos podem ser descritos apenas conforme a cobertura do próprio recorte territorial/ANFIR quando essa evidência existir.
- "Oportunidade comercial" em sentido analítico é uma inferência/recomendação, não a entidade Oportunidade do CRM. Pode indicar sinais comerciais sustentados pelos dados, deixando claro que são inferências.
- Cliente só pode ser chamado de ativo/inativo quando esse status estiver explicitamente presente na evidência consultada. Status de registro ANFIR não prova status do cliente no CRM.
- Status operacional, documental ou ANFIR não prova venda, aceite, negócio concluído, relacionamento comercial ativo ou entrega.
- Nesta camada factual, não use "maioria", "predominante", "predominantes", "líder", "líderes", "domina", "dominam", "dominante" ou equivalentes para descrever distribuição. Informe sempre contagens e, quando útil, percentuais sobre o universo total do recorte.
- Quando a cobertura de um campo for parcial, informe a contagem exata sobre o universo total ou qualifique explicitamente como "entre os registros preenchidos".
- Preserve ausências e qualidade dos dados. Se um valor de fabricante/modelo/status tiver grafia anômala ou cobertura parcial, descreva a limitação sem normalizar silenciosamente o dado como se fosse completo.
- CAMPO AUSENTE NÃO SIGNIFICA OBJETO AUSENTE: modelo, fabricante, status ou qualquer outro campo vazio/nulo significa apenas "não registrado/não informado na fonte". Nunca conclua que o cliente não possui aquele item, equipamento, condição ou característica no mundo real.
- Ausência de modelo, fabricante ou outro campo pode sustentar somente recomendação de qualificação/atualização da base ou investigação comercial para preencher a informação. Por si só, não sustenta oportunidade de venda, renovação, substituição, modernização, conversão, ganho de share ou oferta de produto.
- Um registro "não frigorífico" não prova que conversão, substituição ou venda de refrigeração seja tecnicamente/comercialmente adequada. Pode recomendar verificar necessidade de refrigeração antes de qualquer oferta.
- Diferencie fato, limitação e inferência/recomendação.
- Responda em português do Brasil, com linguagem comercial clara e direta.
"""


def _evidencias_atendidas(metadados: dict[str, Any]) -> set[str]:
    valores = metadados.get("evidencias_atendidas") or []
    return {str(item) for item in valores if str(item)}


def _dominios_nao_consultados(evidencias: set[str]) -> list[str]:
    return sorted(DOMINIOS_FACTUAIS - evidencias)


def _reexecutar_fontes_cti(
    metadados: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
) -> list[dict[str, Any]]:
    fontes: list[dict[str, Any]] = []
    assinaturas: set[str] = set()

    for item in metadados.get("ferramentas") or []:
        if not isinstance(item, dict) or item.get("tipo") != "CTI":
            continue
        ferramenta = str(item.get("ferramenta") or "").strip()
        argumentos = item.get("argumentos") or {}
        if not ferramenta or not isinstance(argumentos, dict):
            continue
        assinatura = f"{ferramenta}:{json.dumps(argumentos, sort_keys=True, ensure_ascii=False, default=str)}"
        if assinatura in assinaturas:
            continue
        assinaturas.add(assinatura)
        resultado = _executar_ferramenta_cti(ferramenta, argumentos, usuario_id, tipo_usuario)
        fontes.append(
            {
                "ferramenta": ferramenta,
                "argumentos": argumentos,
                "resultado": resultado,
            }
        )
    return fontes


def sintetizar_fatos_execucao(
    pergunta_atual: str,
    metadados: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
) -> tuple[str | None, dict[str, Any]]:
    evidencias = _evidencias_atendidas(metadados)
    if not evidencias:
        return None, {"controle_sintese_factual": "nao_aplicada_sem_evidencias"}
    if "web" in evidencias:
        return None, {"controle_sintese_factual": "adiada_para_ia003_com_web"}

    fontes = _reexecutar_fontes_cti(metadados, usuario_id, tipo_usuario)
    if not fontes:
        return None, {"controle_sintese_factual": "nao_aplicada_sem_fontes_cti_reexecutaveis"}

    payload = {
        "PERGUNTA_ATUAL": pergunta_atual,
        "EVIDENCIAS_ATENDIDAS": sorted(evidencias),
        "DOMINIOS_NAO_CONSULTADOS": _dominios_nao_consultados(evidencias),
        "EVIDENCIAS_EXECUCAO": fontes,
    }

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise IAComercialOpenAIError(
            "OPENAI_API_KEY não está configurada no backend.",
            codigo="OPENAI_KEY_MISSING",
        )

    try:
        client = OpenAI(api_key=api_key, timeout=120.0, max_retries=1)
        resposta = client.responses.create(
            model=SYNTHESIS_MODEL,
            instructions=INSTRUCOES_SINTESE_FATUAL,
            input=[
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False, default=str),
                }
            ],
            store=False,
        )
    except IAComercialOpenAIError:
        raise
    except Exception as exc:
        raise _classificar_falha_openai(exc) from exc

    texto = str(getattr(resposta, "output_text", "") or "").strip()
    if not texto:
        raise IAComercialOpenAIError(
            "A síntese factual não produziu uma resposta textual.",
            codigo="OPENAI_EMPTY_SYNTHESIS",
        )

    uso = getattr(resposta, "usage", None)
    return texto, {
        "controle_sintese_factual": "reconstruida_pergunta_e_fontes_execucao",
        "sintese_factual_response_id": getattr(resposta, "id", None),
        "sintese_factual_tokens_entrada": getattr(uso, "input_tokens", None),
        "sintese_factual_tokens_saida": getattr(uso, "output_tokens", None),
        "sintese_factual_fontes_reexecutadas": len(fontes),
        "sintese_factual_dominios_nao_consultados": _dominios_nao_consultados(evidencias),
    }
