from __future__ import annotations

from typing import Any

from . import ia_comercial_auditoria_evidencial as _auditoria_base
from . import ia_comercial_ia010_auditoria_patch as _patch

_ORIGINAL_RECLASSIFICAR = _patch._reclassificar_fluxo_anexo

_ADICIONAIS: dict[str, tuple[str, ...]] = {
    "WEB": (
        "thermo king: referência objetiva por capacidade/volume",
        "thermo king: referencia objetiva por capacidade/volume",
        "frigo king: o que dá para afirmar agora",
        "frigo king: o que da para afirmar agora",
    ),
    "INFERENCIA": (
        "como eu estruturaria a “equivalência em capacidade e operação”",
        "como eu estruturaria a \"equivalência em capacidade e operação\"",
        "como eu estruturaria a equivalência em capacidade e operação",
        "como eu estruturaria a equivalencia em capacidade e operacao",
        "método correto",
        "metodo correto",
    ),
    "CONTROLE": (
        "para eu finalizar o comparativo como você pediu",
        "para eu finalizar o comparativo como voce pediu",
        "me confirme 1 coisa",
    ),
}

_novos: list[tuple[str, tuple[str, ...]]] = []
for _secao, _marcadores in _patch._MARCADORES_ANEXO:
    extras = _ADICIONAIS.get(_secao, ())
    _novos.append((_secao, tuple(dict.fromkeys(tuple(_marcadores) + tuple(extras)))))
_patch._MARCADORES_ANEXO = tuple(_novos)


def _ids_web_por_url_literal(texto: str, origens: list[dict[str, Any]], ids_web: list[str]) -> list[str]:
    alvo = str(texto or "")
    compativeis: list[str] = []
    permitidos = set(ids_web)
    for origem in origens:
        origem_id = str(origem.get("id") or "")
        url = str(origem.get("url") or "")
        if origem_id in permitidos and url and url in alvo:
            compativeis.append(origem_id)
    return compativeis


def _reclassificar_com_heranca_web(resultado: dict[str, Any], resposta_texto: str, metadados: dict[str, Any]) -> None:
    _ORIGINAL_RECLASSIFICAR(resultado, resposta_texto, metadados)

    auditoria = resultado.get("auditoria_evidencial")
    if not isinstance(auditoria, dict):
        return
    origens = [item for item in (auditoria.get("origens_execucao") or []) if isinstance(item, dict)]
    afirmacoes = [item for item in (auditoria.get("afirmacoes") or []) if isinstance(item, dict)]
    if not afirmacoes:
        return

    ids_web = _patch._ids_por_tipo(origens, "WEB")
    if not ids_web:
        return

    eventos = _patch._eventos_secoes(resposta_texto)
    posicoes = _patch._posicoes_afirmacoes(resposta_texto, afirmacoes)
    web_ativos: list[str] = []

    for afirmacao, posicao in zip(afirmacoes, posicoes):
        secao = _patch._secao_na_posicao(eventos, posicao)
        if secao != "WEB":
            if secao in {"ANEXO", "CTI", "INFERENCIA", "CONTROLE"}:
                web_ativos = []
            continue
        if afirmacao.get("tipo") != "FATO_WEB":
            continue

        texto = str(afirmacao.get("texto") or "")
        compativeis = _ids_web_por_url_literal(texto, origens, ids_web)
        if not compativeis:
            compativeis = _auditoria_base._ids_web_por_texto(texto, origens, ids_web)

        if compativeis:
            web_ativos = list(dict.fromkeys(compativeis))
            afirmacao["fontes_evidencia"] = list(web_ativos)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
        elif web_ativos and afirmacao.get("status_rastreabilidade") != "RASTREAVEL":
            afirmacao["fontes_evidencia"] = list(web_ativos)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"

    totais = auditoria.setdefault("totais", {})
    totais["afirmacoes_sem_evidencia_explicita"] = sum(
        1
        for item in afirmacoes
        if item.get("tipo") != "INFERENCIA_RECOMENDACAO"
        and item.get("status_rastreabilidade") != "RASTREAVEL"
    )
    totais["inferencias_recomendacoes"] = sum(
        1 for item in afirmacoes if item.get("tipo") == "INFERENCIA_RECOMENDACAO"
    )
    resultado["auditoria_afirmacoes_sem_evidencia"] = totais["afirmacoes_sem_evidencia_explicita"]


_patch._reclassificar_fluxo_anexo = _reclassificar_com_heranca_web
