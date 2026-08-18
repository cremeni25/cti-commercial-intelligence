from __future__ import annotations

from typing import Any

from . import ia_comercial_auditoria_evidencial as _auditoria_base
from . import ia_comercial_auditoria_proveniencia as _proveniencia


_ORIGINAL_CONSTRUIR = _proveniencia.construir_auditoria_evidencial


_MARCADORES_ANEXO: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "CONTROLE",
        (
            "a pergunta original foi",
            "nesta execução, as evidências",
            "nesta execucao, as evidencias",
        ),
    ),
    (
        "ANEXO",
        (
            "o que o arquivo contém",
            "o que o arquivo contem",
            "análise do arquivo",
            "analise do arquivo",
            "evidência do anexo",
            "evidencia do anexo",
            "fatos do anexo",
            "fatos documentais",
        ),
    ),
    (
        "CTI",
        (
            "fatos internos cti",
            "dados internos cti",
            "evidência desta execução",
            "evidencia desta execucao",
        ),
    ),
    (
        "WEB",
        (
            "fatos externos verificados",
            "pesquisa na web",
            "pesquisa web",
            "fontes web",
            "evidência pública",
            "evidencia publica",
        ),
    ),
    (
        "INFERENCIA",
        (
            "como essas informações podem ser utilizadas",
            "como essas informacoes podem ser utilizadas",
            "comparação prática",
            "comparacao pratica",
            "comparação técnica",
            "comparacao tecnica",
            "recomendações",
            "recomendacoes",
            "pontos positivos relativos",
            "pontos positivos",
            "pontos negativos / riscos",
            "pontos negativos relativos",
            "pontos negativos",
            "implicação objetiva",
            "implicacao objetiva",
            "vantagens e riscos",
        ),
    ),
)

_MARCADORES_CONTROLE_AFIRMACAO = (
    "nenhuma consulta web",
    "não foi consultada evidência web",
    "nao foi consultada evidencia web",
    "não foram realizadas consultas externas",
    "nao foram realizadas consultas externas",
    "sem consulta web",
)

_MARCADORES_ANEXO_DIRETO = (
    "o anexo",
    "no anexo",
    "do anexo",
    "seu anexo",
    "pdf anexo",
    "arquivo anexo",
    "o pdf",
    "no pdf",
    "do pdf",
    "o arquivo",
    "no arquivo",
    "do arquivo",
    "tabela do anexo",
    "conforme a tabela do anexo",
    "o próprio documento",
    "o proprio documento",
)

_MARCADORES_INFERENCIA_DIRETA = (
    "recomenda",
    "recomendação",
    "recomendacao",
    "priorizar",
    "usar o ",
    "usar os ",
    "escolher ",
    "equivalência mais segura",
    "equivalencia mais segura",
    "isso permite comparar",
    "ponto de comparação",
    "ponto de comparacao",
    "fortalece ",
    "risco ",
    "risco de ",
    "não dá para fechar",
    "nao da para fechar",
    "não cravar",
    "nao cravar",
    "mais defensável",
    "mais defensavel",
    "deve ",
    "deveria ",
)


def _ids_por_tipo(origens: list[dict[str, Any]], tipo: str) -> list[str]:
    return [str(item.get("id")) for item in origens if item.get("tipo") == tipo and item.get("id")]


def _eventos_secoes(resposta_texto: str) -> list[tuple[int, str]]:
    texto = str(resposta_texto or "").casefold()
    eventos: list[tuple[int, str]] = []
    for secao, marcadores in _MARCADORES_ANEXO:
        for marcador in marcadores:
            inicio = 0
            while True:
                posicao = texto.find(marcador, inicio)
                if posicao < 0:
                    break
                eventos.append((posicao, secao))
                inicio = posicao + len(marcador)
    eventos.sort(key=lambda item: item[0])
    return eventos


def _secao_na_posicao(eventos: list[tuple[int, str]], posicao: int) -> str | None:
    atual: str | None = None
    for pos_evento, secao in eventos:
        if pos_evento > posicao:
            break
        atual = secao
    return atual


def _posicoes_afirmacoes(resposta_texto: str, afirmacoes: list[dict[str, Any]]) -> list[int]:
    texto = str(resposta_texto or "").casefold()
    cursor = 0
    posicoes: list[int] = []
    for afirmacao in afirmacoes:
        alvo = str(afirmacao.get("texto") or "").strip().casefold()
        if not alvo:
            posicoes.append(cursor)
            continue
        posicao = texto.find(alvo, cursor)
        if posicao < 0:
            posicao = texto.find(alvo)
        if posicao < 0:
            posicao = cursor
        posicoes.append(posicao)
        cursor = max(cursor, posicao + len(alvo))
    return posicoes


def _eh_estrutura(texto: str) -> bool:
    limpo = str(texto or "").lstrip()
    return limpo.startswith("#")


def _parece_anexo_direto(normalizado: str) -> bool:
    return any(marcador in normalizado for marcador in _MARCADORES_ANEXO_DIRETO)


def _parece_inferencia(normalizado: str) -> bool:
    return any(marcador in normalizado for marcador in _MARCADORES_INFERENCIA_DIRETA)


def _tornar_inferencia(afirmacao: dict[str, Any], fontes_base: list[str]) -> None:
    afirmacao["tipo"] = "INFERENCIA_RECOMENDACAO"
    afirmacao["fontes_evidencia"] = []
    afirmacao["derivada_de"] = list(dict.fromkeys(list(afirmacao.get("derivada_de") or []) + fontes_base))
    afirmacao.setdefault("premissas_fatuais_exigidas", [])
    afirmacao.setdefault("premissas_fatuais_nao_sustentadas", [])
    if afirmacao.get("status_rastreabilidade") != "BASE_PARCIAL":
        afirmacao["status_rastreabilidade"] = "RASTREAVEL" if afirmacao["derivada_de"] else "SEM_BASE_EXPLICITA"


def _tornar_controle(afirmacao: dict[str, Any], ids_controle: list[str]) -> None:
    afirmacao["tipo"] = "FATO_CONTROLE"
    afirmacao["fontes_evidencia"] = list(ids_controle)
    afirmacao["derivada_de"] = []
    afirmacao["status_rastreabilidade"] = "RASTREAVEL"


def _reclassificar_fluxo_anexo(resultado: dict[str, Any], resposta_texto: str, metadados: dict[str, Any]) -> None:
    # Regra crítica: não toca na auditoria homologada de execuções sem anexos.
    if not any(isinstance(item, dict) for item in (metadados.get("anexos") or [])):
        return

    auditoria = resultado.get("auditoria_evidencial")
    if not isinstance(auditoria, dict):
        return
    origens = [item for item in (auditoria.get("origens_execucao") or []) if isinstance(item, dict)]
    afirmacoes = [item for item in (auditoria.get("afirmacoes") or []) if isinstance(item, dict)]
    if not afirmacoes:
        return

    ids_web = _ids_por_tipo(origens, "WEB")
    ids_cti = _ids_por_tipo(origens, "CTI")
    ids_anexo = _ids_por_tipo(origens, "ANEXO_TEMPORARIO")
    ids_controle = _ids_por_tipo(origens, "CONTROLE_EXECUCAO")
    ids_memoria = _ids_por_tipo(origens, "CONHECIMENTO_IA")
    fontes_base = list(dict.fromkeys(ids_anexo + ids_memoria + ids_cti + ids_web))

    eventos = _eventos_secoes(resposta_texto)
    posicoes = _posicoes_afirmacoes(resposta_texto, afirmacoes)

    for afirmacao, posicao in zip(afirmacoes, posicoes):
        texto_afirmacao = str(afirmacao.get("texto") or "")
        normalizado = texto_afirmacao.casefold()
        secao = _secao_na_posicao(eventos, posicao)

        # Títulos/estrutura pertencem ao controle da resposta, não ao conjunto de fatos.
        if _eh_estrutura(texto_afirmacao) and ids_controle:
            _tornar_controle(afirmacao, ids_controle)
            continue

        # Ausência de consulta web é um estado da execução, nunca um fato web.
        if any(marcador in normalizado for marcador in _MARCADORES_CONTROLE_AFIRMACAO) and ids_controle:
            _tornar_controle(afirmacao, ids_controle)
            continue

        if secao == "CONTROLE" and ids_controle:
            _tornar_controle(afirmacao, ids_controle)
            continue

        # Comparações, vantagens, riscos, escolhas e recomendações são síntese derivada,
        # mesmo quando repetem partes do documento ou de uma fonte externa.
        if secao == "INFERENCIA" or _parece_inferencia(normalizado):
            _tornar_inferencia(afirmacao, fontes_base)
            continue

        # Referência textual inequívoca ao documento tem precedência sobre a seção herdada.
        if _parece_anexo_direto(normalizado) and ids_anexo:
            afirmacao["tipo"] = "FATO_ANEXO"
            afirmacao["fontes_evidencia"] = list(ids_anexo)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if secao == "ANEXO" and ids_anexo:
            afirmacao["tipo"] = "FATO_ANEXO"
            afirmacao["fontes_evidencia"] = list(ids_anexo)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if secao == "CTI" and ids_cti:
            afirmacao["tipo"] = "FATO_CTI"
            afirmacao["fontes_evidencia"] = list(ids_cti)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if secao == "WEB" and ids_web:
            compativeis = _auditoria_base._ids_web_por_texto(texto_afirmacao, origens, ids_web)
            if compativeis:
                afirmacao["tipo"] = "FATO_WEB"
                afirmacao["fontes_evidencia"] = list(compativeis)
                afirmacao["derivada_de"] = []
                afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            # Sem fonte compatível, preserva o guardrail anterior em vez de
            # atribuir genericamente todas as URLs a uma afirmação nomeada.
            continue

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
    resultado["auditoria_afirmacoes_total"] = len(afirmacoes)
    resultado["auditoria_afirmacoes_sem_evidencia"] = totais["afirmacoes_sem_evidencia_explicita"]
    resultado["auditoria_inferencias_base_parcial"] = totais["inferencias_base_parcial"]


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
    _reclassificar_fluxo_anexo(resultado, resposta_texto, metadados)
    return resultado


_proveniencia.construir_auditoria_evidencial = construir_auditoria_evidencial
_auditoria_base.construir_auditoria_evidencial = construir_auditoria_evidencial
