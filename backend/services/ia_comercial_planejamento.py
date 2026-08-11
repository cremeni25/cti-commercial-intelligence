from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

from services import ia_comercial_agente_crm as crm
from services.ia_comercial_cti import IAComercialOpenAIError, _classificar_falha_openai


PLANNING_MODEL = os.getenv("OPENAI_AGENT_MODEL", os.getenv("OPENAI_WEB_MODEL", "gpt-4.1-mini"))

_MARCADORES_PLANEJAMENTO = (
    "recomenda", "recomendação", "recomendacoes", "recomendações", "plano", "planeje", "planejamento",
    "prioridade", "priorize", "estratégia", "estrategia", "próximos passos", "proximos passos",
    "o que devo fazer", "o que fazer", "qual ação", "qual acao", "ações", "acoes", "como agir",
    "como avançar", "como avancar", "decisão", "decisao",
)

_MARCADORES_OPORTUNIDADE_ANALITICA = (
    "oportunidade comercial",
    "oportunidades comerciais",
    "oportunidade futura",
    "oportunidades futuras",
    "sinal de oportunidade",
    "sinais de oportunidade",
    "potencial de oportunidade",
    "potenciais oportunidades",
)

_MARCADORES_OPORTUNIDADE_CRM = (
    "oportunidades do crm",
    "oportunidade do crm",
    "pipeline",
    "oportunidade registrada",
    "oportunidades registradas",
    "oportunidade vinculada",
    "oportunidades vinculadas",
    "oportunidade relacionada",
    "oportunidades relacionadas",
    "status da oportunidade",
    "estágio da oportunidade",
    "estagio da oportunidade",
    "probabilidade da oportunidade",
    "oportunidades abertas",
    "oportunidades ganhas",
    "oportunidades perdidas",
)

_ORIGINAL_FONTES_BASE_IA007 = crm._ORIGINAL_FONTES_REQUERIDAS


def _fontes_requeridas_semantica_ia007(mensagem: str) -> set[str]:
    """Evita transformar oportunidade futura/analítica em consulta da entidade CRM."""
    requeridas = set(_ORIGINAL_FONTES_BASE_IA007(mensagem))
    texto = str(mensagem or "").casefold()
    oportunidade_analitica = any(marcador in texto for marcador in _MARCADORES_OPORTUNIDADE_ANALITICA)
    oportunidade_crm = any(marcador in texto for marcador in _MARCADORES_OPORTUNIDADE_CRM)
    if oportunidade_analitica and not oportunidade_crm:
        requeridas.discard("oportunidades")
    return requeridas


# A cadeia IA-003/IA-004 chama _fontes_requeridas_crm, que consulta este
# original capturado. A substituição mantém a interface e apenas corrige a
# semântica de oportunidade futura em perguntas de planejamento.
crm._ORIGINAL_FONTES_REQUERIDAS = _fontes_requeridas_semantica_ia007


_INSTRUCOES_PLANEJAMENTO = """Você é a camada IA-007 de planejamento comercial do CTI.
Receba somente a pergunta atual, a resposta já entregue e a auditoria evidencial da MESMA execução.
Sua função é transformar recomendações sustentadas em um plano comercial ordenado; não criar fatos novos.

REGRAS OBRIGATÓRIAS:
- Responda SOMENTE JSON válido, sem markdown.
- Use somente afirmações A# existentes em AUDITORIA como fundamentos.
- Não use afirmações com status SEM_EVIDENCIA_EXPLICITA como fundamento factual.
- Se um fundamento estiver BASE_PARCIAL, mantenha a ação qualificada como BASE_PARCIAL e descreva a lacuna.
- Não recomende avançar/converter oportunidade cujo estado factual seja GANHO, PERDIDO, CANCELADO ou ENCERRADO.
- "Oportunidade futura" ou "oportunidade comercial" pode ser recomendação prospectiva; não afirme que existe ou não existe entidade Oportunidade no CRM sem evidência explícita dessa entidade.
- Resultado vazio de busca textual não prova ausência de relacionamento com outra entidade.
- Diferencie ação operacional imediata, acompanhamento e oportunidade futura.
- Não invente prazo em dias, valor, cliente, produto, venda, probabilidade ou resultado quantitativo.
- Horizonte deve ser somente IMEDIATO, CURTO_PRAZO ou MEDIO_PRAZO.
- Prioridade deve ser somente ALTA, MEDIA ou BAIXA.
- Cada ação deve ter pelo menos um fundamento A#.

FORMATO:
{
  "objetivo": "...",
  "acoes": [
    {
      "ordem": 1,
      "prioridade": "ALTA",
      "acao": "...",
      "horizonte": "IMEDIATO",
      "dependencias": ["..."],
      "riscos": ["..."],
      "resultado_esperado": "...",
      "fundamentos": ["A1"],
      "qualificacao_evidencial": "EVIDENCIA_COMPLETA"
    }
  ]
}
"""


def requer_planejamento(pergunta: str) -> bool:
    texto = str(pergunta or "").casefold()
    return bool(texto) and any(marcador in texto for marcador in _MARCADORES_PLANEJAMENTO)


def _afirmacoes_por_id(auditoria: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in (auditoria.get("afirmacoes") or [])
        if isinstance(item, dict) and item.get("id")
    }


def _oportunidade_encerrada(auditoria: dict[str, Any]) -> bool:
    padrao = re.compile(
        r"\boportunidade\b.*\b(GANHO|GANHA|PERDIDO|PERDIDA|CANCELADO|CANCELADA|ENCERRADO|ENCERRADA)\b",
        re.I,
    )
    return any(
        padrao.search(str(item.get("texto") or ""))
        for item in (auditoria.get("afirmacoes") or [])
        if isinstance(item, dict) and item.get("tipo") == "FATO_CTI"
    )


def _normalizar_lista(valor: Any, limite: int = 5) -> list[str]:
    if not isinstance(valor, list):
        return []
    return [str(item).strip()[:500] for item in valor if str(item).strip()][:limite]


def validar_plano(plano: dict[str, Any], auditoria: dict[str, Any]) -> dict[str, Any]:
    afirmacoes = _afirmacoes_por_id(auditoria)
    oportunidade_encerrada = _oportunidade_encerrada(auditoria)
    acoes_validas: list[dict[str, Any]] = []

    for item in plano.get("acoes") or []:
        if not isinstance(item, dict):
            continue
        acao = str(item.get("acao") or "").strip()
        if not acao:
            continue

        fundamentos = [str(x) for x in (item.get("fundamentos") or []) if str(x) in afirmacoes]
        fundamentos = list(dict.fromkeys(fundamentos))
        fundamentos_validos = [
            fid
            for fid in fundamentos
            if str(afirmacoes[fid].get("status_rastreabilidade") or "") != "SEM_EVIDENCIA_EXPLICITA"
        ]
        if not fundamentos_validos:
            continue

        acao_norm = acao.casefold()
        if oportunidade_encerrada and "oportunidade" in acao_norm and any(
            termo in acao_norm for termo in ("avanç", "avanc", "convert")
        ):
            continue

        status_fundamentos = {
            str(afirmacoes[fid].get("status_rastreabilidade") or "") for fid in fundamentos_validos
        }
        qualificacao = "BASE_PARCIAL" if "BASE_PARCIAL" in status_fundamentos else "EVIDENCIA_COMPLETA"
        lacunas: list[str] = []
        if qualificacao == "BASE_PARCIAL":
            for fid in fundamentos_validos:
                lacunas.extend(
                    str(x) for x in (afirmacoes[fid].get("premissas_fatuais_nao_sustentadas") or [])
                )
            lacunas = list(dict.fromkeys(lacunas))

        prioridade = str(item.get("prioridade") or "MEDIA").upper()
        if prioridade not in {"ALTA", "MEDIA", "BAIXA"}:
            prioridade = "MEDIA"
        horizonte = str(item.get("horizonte") or "CURTO_PRAZO").upper()
        if horizonte not in {"IMEDIATO", "CURTO_PRAZO", "MEDIO_PRAZO"}:
            horizonte = "CURTO_PRAZO"

        acoes_validas.append(
            {
                "ordem": len(acoes_validas) + 1,
                "prioridade": prioridade,
                "acao": acao[:1200],
                "horizonte": horizonte,
                "dependencias": _normalizar_lista(item.get("dependencias")),
                "riscos": _normalizar_lista(item.get("riscos")),
                "resultado_esperado": str(item.get("resultado_esperado") or "").strip()[:1000],
                "fundamentos": fundamentos_validos,
                "qualificacao_evidencial": qualificacao,
                "lacunas_evidenciais": lacunas,
            }
        )

    return {
        "objetivo": str(
            plano.get("objetivo") or "Plano comercial baseado nas evidências da execução atual."
        ).strip()[:1200],
        "acoes": acoes_validas[:8],
        "oportunidade_encerrada_detectada": oportunidade_encerrada,
    }


def _renderizar_plano(plano: dict[str, Any]) -> str:
    acoes = plano.get("acoes") or []
    if not acoes:
        return ""
    linhas = ["PLANO COMERCIAL ESTRUTURADO", str(plano.get("objetivo") or "").strip()]
    for item in acoes:
        qualificacao = str(item.get("qualificacao_evidencial") or "EVIDENCIA_COMPLETA")
        linhas.append(
            f"{item['ordem']}. [{item['prioridade']} | {item['horizonte']}] {item['acao']} "
            f"(base: {', '.join(item['fundamentos'])}; evidência: {qualificacao})"
        )
        if item.get("dependencias"):
            linhas.append("   Dependências: " + "; ".join(item["dependencias"]))
        if item.get("riscos"):
            linhas.append("   Riscos: " + "; ".join(item["riscos"]))
        if item.get("resultado_esperado"):
            linhas.append("   Resultado esperado: " + item["resultado_esperado"])
        if item.get("lacunas_evidenciais"):
            linhas.append("   Lacunas evidenciais: " + ", ".join(item["lacunas_evidenciais"]))
    return "\n".join(linhas).strip()


def construir_planejamento_comercial(
    pergunta_atual: str,
    resposta_texto: str,
    metadados: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if not requer_planejamento(pergunta_atual):
        return resposta_texto, {
            "controle_planejamento_comercial": "ia007_nao_requerido",
            "planejamento_comercial_ativo": False,
        }

    auditoria = metadados.get("auditoria_evidencial") or {}
    if not auditoria.get("afirmacoes"):
        return resposta_texto, {
            "controle_planejamento_comercial": "ia007_sem_auditoria_suficiente",
            "planejamento_comercial_ativo": False,
        }

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise IAComercialOpenAIError(
            "OPENAI_API_KEY não está configurada no backend.",
            codigo="OPENAI_KEY_MISSING",
        )

    entrada = {
        "PERGUNTA_ATUAL": pergunta_atual,
        "RESPOSTA_AUDITADA": resposta_texto,
        "AUDITORIA": {
            "afirmacoes": auditoria.get("afirmacoes") or [],
            "evidencias_requeridas": auditoria.get("evidencias_requeridas") or [],
            "evidencias_atendidas": auditoria.get("evidencias_atendidas") or [],
            "historico_conta_como_evidencia": False,
        },
    }

    try:
        client = OpenAI(api_key=api_key, timeout=90.0, max_retries=1)
        resposta = client.responses.create(
            model=PLANNING_MODEL,
            instructions=_INSTRUCOES_PLANEJAMENTO,
            input=json.dumps(entrada, ensure_ascii=False, default=str),
            store=False,
        )
        bruto = str(getattr(resposta, "output_text", "") or "").strip()
        plano_bruto = json.loads(bruto)
    except json.JSONDecodeError as exc:
        raise IAComercialOpenAIError(
            "A IA não conseguiu estruturar o plano comercial com segurança.",
            codigo="AGENT_PLANNING_INVALID_JSON",
            detalhe_tecnico=str(exc),
        ) from exc
    except IAComercialOpenAIError:
        raise
    except Exception as exc:
        raise _classificar_falha_openai(exc) from exc

    plano = validar_plano(plano_bruto if isinstance(plano_bruto, dict) else {}, auditoria)
    renderizado = _renderizar_plano(plano)
    texto_final = resposta_texto if not renderizado else renderizado

    return texto_final, {
        "controle_planejamento_comercial": "ia007_plano_validado_por_evidencia",
        "planejamento_comercial_ativo": True,
        "plano_comercial": plano,
        "planejamento_acoes_total": len(plano.get("acoes") or []),
        "planejamento_modelo": PLANNING_MODEL,
        "planejamento_store": False,
        "planejamento_historico_como_evidencia": False,
        "controle_oportunidade_futura": "analitica_nao_entidade_crm_sem_pedido_explicito",
        "controle_resposta_planejamento": "somente_plano_validado_sem_texto_livre_previo",
    }
