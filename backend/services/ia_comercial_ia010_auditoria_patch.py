from __future__ import annotations

from typing import Any

from . import ia_comercial_auditoria_evidencial as _auditoria_base
from . import ia_comercial_auditoria_proveniencia as _proveniencia


_ORIGINAL_SECAO = _proveniencia._secao_implicita
_ORIGINAL_CONSTRUIR = _proveniencia.construir_auditoria_evidencial


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _secao_ia010(texto: str, atual: str | None) -> str | None:
    normalizado = _normalizar(texto)

    if any(marcador in normalizado for marcador in (
        "a pergunta original foi",
        "nesta execução, as evidências",
        "nesta execucao, as evidencias",
    )):
        return "CONTROLE"

    if any(marcador in normalizado for marcador in (
        "análise do arquivo",
        "analise do arquivo",
        "evidência do anexo",
        "evidencia do anexo",
        "pdf anexo",
        "arquivo anexo",
        "o que ele contém",
        "o que ele contem",
    )):
        return "ANEXO"

    if any(marcador in normalizado for marcador in (
        "recomendações",
        "recomendacoes",
        "pontos positivos relativos",
        "pontos negativos / riscos",
        "pontos negativos relativos",
        "implicação objetiva",
        "implicacao objetiva",
    )):
        return "INFERENCIA"

    return _ORIGINAL_SECAO(texto, atual)


def _adicionar_memorias(resultado: dict[str, Any], metadados: dict[str, Any]) -> None:
    auditoria = resultado.get("auditoria_evidencial")
    if not isinstance(auditoria, dict):
        return
    origens = [item for item in (auditoria.get("origens_execucao") or []) if isinstance(item, dict)]
    existentes = {str(item.get("id")) for item in origens if item.get("id")}
    memorias = [item for item in (metadados.get("conhecimento_semantico_usado") or []) if isinstance(item, dict)]
    for indice, memoria in enumerate(memorias, start=1):
        origem_id = f"MEMORIA_{indice}"
        if origem_id in existentes:
            continue
        origens.append({
            "id": origem_id,
            "tipo": "CONHECIMENTO_IA",
            "documento_id": memoria.get("documento_id"),
            "nome": memoria.get("nome"),
            "sha256": memoria.get("sha256"),
            "escopo": memoria.get("escopo"),
            "verdade_operacional": False,
            "execucao_atual": True,
        })
    auditoria["origens_execucao"] = origens
    totais = auditoria.setdefault("totais", {})
    totais["origens"] = len(origens)
    resultado["auditoria_fontes_total"] = len(origens)


def construir_auditoria_evidencial(
    resposta_texto: str,
    metadados: dict[str, Any],
    pergunta_atual: str,
) -> dict[str, Any]:
    resultado = _ORIGINAL_CONSTRUIR(resposta_texto, metadados, pergunta_atual)
    _adicionar_memorias(resultado, metadados)
    return resultado


_proveniencia._secao_implicita = _secao_ia010
_proveniencia.construir_auditoria_evidencial = construir_auditoria_evidencial
_auditoria_base.construir_auditoria_evidencial = construir_auditoria_evidencial
