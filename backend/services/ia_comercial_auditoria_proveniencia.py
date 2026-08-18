from __future__ import annotations

from typing import Any

from . import ia_comercial_auditoria_evidencial as _auditoria


_ORIGINAL_CONSTRUIR_AUDITORIA = _auditoria.construir_auditoria_evidencial


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _secao_implicita(texto: str, atual: str | None) -> str | None:
    """Infere proveniência narrativa sem interferir no roteamento de fontes."""
    normalizado = _normalizar(texto)

    marcadores_anexo = (
        "o que o arquivo contém",
        "o que o arquivo contem",
        "extraído do próprio pdf",
        "extraido do proprio pdf",
        "extraído do anexo",
        "extraido do anexo",
        "conteúdo do anexo",
        "conteudo do anexo",
        "dados do anexo",
    )
    marcadores_web = (
        "pesquisa na web",
        "pesquisa web",
        "fontes web",
        "fonte web",
        "informações externas",
        "informacoes externas",
        "mercado externo",
        "dados externos",
        "fatos externos verificados",
    )
    marcadores_sem_web = (
        "nenhuma consulta web",
        "não foi consultada evidência web",
        "nao foi consultada evidencia web",
        "não foram realizadas consultas externas",
        "nao foram realizadas consultas externas",
        "sem consulta web",
    )
    marcadores_cti = (
        "fatos internos cti",
        "evidência desta execução",
        "evidencia desta execucao",
        "universo histórico autorizado pelo cti",
        "universo historico autorizado pelo cti",
        "dados internos cti",
        "dados do cti",
        "registros históricos no cti",
        "registros historicos no cti",
        "ranking interno cti",
        "histórico anfir disponível no cti",
        "historico anfir disponivel no cti",
        "histórico anfir do cti",
        "historico anfir do cti",
        "banco do cti",
    )
    marcadores_inferencia = (
        "como essas informações podem ser utilizadas no cti",
        "como essas informacoes podem ser utilizadas no cti",
        "inferências/recomendações",
        "inferencias/recomendacoes",
        "utilizações recomendadas",
        "utilizacoes recomendadas",
        "melhor uso prático",
        "melhor uso pratico",
        "cruzamento entre cti e web",
        "comparando os dados internos",
        "comparação entre os dados internos",
        "comparacao entre os dados internos",
        "assim, o ranking interno",
        "portanto, o ranking interno",
    )

    if any(marcador in normalizado for marcador in marcadores_inferencia):
        return "INFERENCIA"
    if any(marcador in normalizado for marcador in marcadores_sem_web):
        return "CONTROLE"
    if any(marcador in normalizado for marcador in marcadores_anexo):
        return "ANEXO"
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


def _adicionar_origens_anexo_e_controle(auditoria: dict[str, Any], metadados: dict[str, Any]) -> None:
    origens = [item for item in (auditoria.get("origens_execucao") or []) if isinstance(item, dict)]
    ids_existentes = {str(item.get("id")) for item in origens if item.get("id")}

    anexos = [item for item in (metadados.get("anexos") or []) if isinstance(item, dict)]
    for indice, anexo in enumerate(anexos, start=1):
        origem_id = f"ANEXO_{indice}"
        if origem_id in ids_existentes:
            continue
        origens.append(
            {
                "id": origem_id,
                "tipo": "ANEXO_TEMPORARIO",
                "nome": str(anexo.get("nome") or f"anexo-{indice}"),
                "mime_type": anexo.get("mime_type"),
                "sha256": anexo.get("sha256"),
                "estrutura": dict(anexo.get("estrutura") or {}),
                "tamanho_bytes": anexo.get("tamanho_bytes"),
                "temporario": bool(anexo.get("temporario", True)),
                "publicado_cti": bool(anexo.get("publicado_cti", False)),
                "execucao_atual": True,
            }
        )
        ids_existentes.add(origem_id)

    if "EXECUCAO_1" not in ids_existentes:
        origens.append(
            {
                "id": "EXECUCAO_1",
                "tipo": "CONTROLE_EXECUCAO",
                "web_requerida": bool(metadados.get("web_requerida", False)),
                "web_fontes_validas": int(metadados.get("web_fontes_validas") or 0),
                "web_urls_auditaveis": list(metadados.get("web_urls_auditaveis") or []),
                "somente_leitura": bool(metadados.get("somente_leitura", False)),
                "controle_anexos": metadados.get("controle_anexos"),
                "execucao_atual": True,
            }
        )

    auditoria["origens_execucao"] = origens


def _tornar_inferencia(afirmacao: dict[str, Any], fontes_base: list[str]) -> None:
    afirmacao["tipo"] = "INFERENCIA_RECOMENDACAO"
    afirmacao["fontes_evidencia"] = []
    afirmacao["derivada_de"] = list(dict.fromkeys(fontes_base))
    afirmacao["premissas_fatuais_exigidas"] = []
    afirmacao["premissas_fatuais_nao_sustentadas"] = []
    afirmacao["status_rastreabilidade"] = "RASTREAVEL" if fontes_base else "SEM_BASE_EXPLICITA"


def _reclassificar_afirmacoes(auditoria: dict[str, Any]) -> None:
    origens = [item for item in (auditoria.get("origens_execucao") or []) if isinstance(item, dict)]
    ids_web = _ids_por_tipo(origens, "WEB")
    ids_cti = _ids_por_tipo(origens, "CTI")
    ids_anexo = _ids_por_tipo(origens, "ANEXO_TEMPORARIO")
    ids_controle = _ids_por_tipo(origens, "CONTROLE_EXECUCAO")
    afirmacoes = [item for item in (auditoria.get("afirmacoes") or []) if isinstance(item, dict)]

    secao: str | None = None
    fontes_base = list(dict.fromkeys(ids_anexo + ids_cti + ids_web))

    for afirmacao in afirmacoes:
        texto = str(afirmacao.get("texto") or "")
        secao = _secao_implicita(texto, secao)
        tipo_original = str(afirmacao.get("tipo") or "")

        if secao == "INFERENCIA" or tipo_original == "INFERENCIA_RECOMENDACAO":
            _tornar_inferencia(afirmacao, fontes_base)
            continue

        if secao == "ANEXO" and ids_anexo:
            afirmacao["tipo"] = "FATO_ANEXO"
            afirmacao["fontes_evidencia"] = list(ids_anexo)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if secao == "CONTROLE" and ids_controle:
            afirmacao["tipo"] = "FATO_CONTROLE"
            afirmacao["fontes_evidencia"] = list(ids_controle)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        # A auditoria base já conhece seções WEB explícitas. Essa informação
        # prevalece sobre a seção narrativa anterior, mas somente quando existe
        # uma fonte web real e auditável na execução.
        if tipo_original == "FATO_WEB":
            if ids_web:
                compativeis = _auditoria._ids_web_por_texto(texto, origens, ids_web)
                afirmacao["tipo"] = "FATO_WEB"
                afirmacao["fontes_evidencia"] = list(compativeis or ids_web)
                afirmacao["derivada_de"] = []
                afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            elif ids_controle:
                afirmacao["tipo"] = "FATO_CONTROLE"
                afirmacao["fontes_evidencia"] = list(ids_controle)
                afirmacao["derivada_de"] = []
                afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if secao == "CTI" and ids_cti:
            afirmacao["tipo"] = "FATO_CTI"
            afirmacao["fontes_evidencia"] = list(ids_cti)
            afirmacao["derivada_de"] = []
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"
            continue

        if tipo_original == "FATO_CTI" and ids_cti:
            afirmacao["fontes_evidencia"] = list(ids_cti)
            afirmacao["status_rastreabilidade"] = "RASTREAVEL"

    totais = auditoria.setdefault("totais", {})
    totais["origens"] = len(origens)
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

    _adicionar_origens_anexo_e_controle(auditoria, metadados)
    _reclassificar_afirmacoes(auditoria)

    totais = auditoria.get("totais") or {}
    resultado["auditoria_afirmacoes_total"] = int(totais.get("afirmacoes") or 0)
    resultado["auditoria_afirmacoes_sem_evidencia"] = int(
        totais.get("afirmacoes_sem_evidencia_explicita") or 0
    )
    resultado["auditoria_inferencias_base_parcial"] = int(
        totais.get("inferencias_base_parcial") or 0
    )
    resultado["auditoria_fontes_total"] = int(totais.get("origens") or 0)
    resultado["controle_proveniencia_evidencia"] = "ia010_anexo_cti_web_inferencia_explicitos"
    return resultado


# O router importa a função diretamente do módulo histórico. Ao substituir a
# referência no módulo durante a inicialização de services, todos os consumidores
# posteriores recebem a versão corrigida sem alterar a API pública existente.
_auditoria.construir_auditoria_evidencial = construir_auditoria_evidencial
