from __future__ import annotations

from typing import Any

from . import ia_comercial_auditoria_evidencial as _auditoria


_ORIGINAL_CONSTRUIR_AUDITORIA = _auditoria.construir_auditoria_evidencial


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _secao_implicita(texto: str, atual: str | None) -> str | None:
    """Infere somente a proveniência narrativa, nunca o domínio consultado.

    Esta camada não roteia perguntas nem escolhe ferramentas. Ela apenas interpreta
    como a resposta final separou fatos internos, fatos externos e comparação entre
    ambos para que a trilha IA-006 não atribua uma afirmação web ao CTI por mera
    coincidência de entidade.
    """
    normalizado = _normalizar(texto)

    marcadores_web = (
        "pesquisa na web",
        "pesquisa web",
        "fontes web",
        "fonte web",
        "informações externas",
        "informacoes externas",
        "mercado externo",
        "dados externos",
    )
    marcadores_cti = (
        "universo histórico autorizado pelo cti",
        "universo historico autorizado pelo cti",
        "dados internos cti",
        "dados do cti",
        "registros históricos no cti",
        "registros historicos no cti",
        "ranking interno cti",
    )
    marcadores_cruzamento = (
        "ranking interno cti e o ranking",
        "comparando os dados internos",
        "comparação entre os dados internos",
        "comparacao entre os dados internos",
        "cruzamento entre cti e web",
        "assim, o ranking interno",
        "portanto, o ranking interno",
    )

    if any(marcador in normalizado for marcador in marcadores_cruzamento):
        return "INFERENCIA"
    if any(marcador in normalizado for marcador in marcadores_web):
        return "WEB"
    if any(marcador in normalizado for marcador in marcadores_cti):
        return "CTI"
    return atual


def _ids_por_tipo(origens: list[dict[str, Any]], tipo: str) -> list[str]:
    return [
        str(origem.get("id"))
        for origem in origens
        if origem.get("tipo") == tipo and origem.get("id")
    ]


def _reclassificar_afirmacoes(auditoria: dict[str, Any]) -> None:
    origens = [item for item in (auditoria.get("origens_execucao") or []) if isinstance(item, dict)]
    ids_web = _ids_por_tipo(origens, "WEB")
    ids_cti = _ids_por_tipo(origens, "CTI")
    afirmacoes = [item for item in (auditoria.get("afirmacoes") or []) if isinstance(item, dict)]

    secao: str | None = None
    for afirmacao in afirmacoes:
        texto = str(afirmacao.get("texto") or "")
        secao = _secao_implicita(texto, secao)

        if secao == "CTI" and ids_cti:
            afirmacao["tipo"] = "FATO_CTI"
            afirmacao["fontes_evidencia"] = list(ids_cti)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if secao == "WEB" and ids_web:
            compativeis = _auditoria._ids_web_por_texto(texto, origens, ids_web)
            # Em uma seção explicitamente externa, a lista de fontes web da
            # execução é a proveniência coletiva quando título/URL não permitem
            # resolver uma única fonte com segurança.
            afirmacao["tipo"] = "FATO_WEB"
            afirmacao["fontes_evidencia"] = list(compativeis or ids_web)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if secao == "INFERENCIA" and (ids_cti or ids_web):
            afirmacao["tipo"] = "INFERENCIA_RECOMENDACAO"
            afirmacao["fontes_evidencia"] = []
            afirmacao["derivada_de"] = list(dict.fromkeys(ids_cti + ids_web))
            afirmacao["premissas_fatuais_exigidas"] = []
            afirmacao["premissas_fatuais_nao_sustentadas"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"

    totais = auditoria.setdefault("totais", {})
    totais["afirmacoes"] = len(afirmacoes)
    totais["afirmacoes_sem_evidencia_explicita"] = sum(
        1
        for item in afirmacoes
        if item.get("tipo") != "INFERENCIA_RECOMENDACAO"
        and item.get("status_rastreabilidade") != "RASTREAVEL"
    )
    totais["inferencias_recomendacoes"] = sum(
        1 for item in afirmacoes if item.get("tipo") == "INFERENCIA_RECOMENDACAO"
    )
    totais["inferencias_base_parcial"] = sum(
        1 for item in afirmacoes if item.get("status_rastreabilidade") == "BASE_PARCIAL"
    )


def construir_auditoria_evidencial(
    resposta_texto: str,
    metadados: dict[str, Any],
    pergunta_atual: str,
) -> dict[str, Any]:
    resultado = _ORIGINAL_CONSTRUIR_AUDITORIA(
        resposta_texto=resposta_texto,
        metadados=metadados,
        pergunta_atual=pergunta_atual,
    )
    auditoria = resultado.get("auditoria_evidencial")
    if not isinstance(auditoria, dict):
        return resultado

    ids_web = _ids_por_tipo(auditoria.get("origens_execucao") or [], "WEB")
    ids_cti = _ids_por_tipo(auditoria.get("origens_execucao") or [], "CTI")
    if not (ids_web and ids_cti):
        return resultado

    _reclassificar_afirmacoes(auditoria)
    totais = auditoria.get("totais") or {}
    resultado["auditoria_afirmacoes_total"] = int(totais.get("afirmacoes") or 0)
    resultado["auditoria_afirmacoes_sem_evidencia"] = int(
        totais.get("afirmacoes_sem_evidencia_explicita") or 0
    )
    resultado["auditoria_inferencias_base_parcial"] = int(
        totais.get("inferencias_base_parcial") or 0
    )
    resultado["controle_proveniencia_evidencia"] = "fonte_explicita_com_secao_narrativa_multifonte"
    return resultado


# O router importa a função diretamente do módulo histórico. Ao substituir a
# referência no módulo durante a inicialização de services, todos os consumidores
# posteriores recebem a versão corrigida sem alterar a API pública existente.
_auditoria.construir_auditoria_evidencial = construir_auditoria_evidencial
