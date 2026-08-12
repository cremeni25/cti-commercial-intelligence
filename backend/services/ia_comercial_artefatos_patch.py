from __future__ import annotations

import re
import unicodedata
from typing import Any

from . import ia_comercial_agente_crm as _agente
from .ia_comercial_artefatos import construir_artefatos, detectar_intencao_artefato, extrair_serie_numerica


_ORIGINAL_GERAR_RESPOSTA = _agente.gerar_resposta_agente


def _normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(ch for ch in bruto if not unicodedata.combining(ch)).casefold()


def _resposta_anterior(historico: list[dict[str, str]]) -> str:
    for item in reversed(historico):
        if item.get("role") == "assistant" and str(item.get("content") or "").strip():
            return str(item["content"])
    return ""


def _separar_blocos_multifonte(texto: str) -> tuple[str, str]:
    linhas = str(texto or "").splitlines()
    indice_web: int | None = None
    marcadores = (
        "externamente",
        "separadamente",
        "em complemento",
        "externo web",
        "ranking externo",
        "pesquisa na web",
    )
    for indice, linha in enumerate(linhas):
        normalizada = _normalizar(linha)
        if any(marcador in normalizada for marcador in marcadores):
            indice_web = indice
            break
    if indice_web is None:
        return str(texto or ""), ""
    return "\n".join(linhas[:indice_web]), "\n".join(linhas[indice_web:])


def _ranking_ordinal(texto: str, limite: int = 10) -> list[dict[str, Any]]:
    dados: list[dict[str, Any]] = []
    for linha in str(texto or "").splitlines():
        limpa = linha.strip()
        match = re.match(r"^(?:[-*•]\s+|(?P<pos>\d+)[.)]\s+)(?P<label>.+?)\s*$", limpa)
        if not match:
            continue
        label = match.group("label").strip()
        if not label or len(label) > 120:
            continue
        # Remove qualificações narrativas, preservando o nome exibido na resposta.
        label = re.sub(r"\s*\([^)]*\)\s*$", "", label).strip().rstrip(".")
        if not label:
            continue
        posicao = len(dados) + 1
        dados.append({"label": label, "valor": float(posicao), "unidade": "posição"})
        if len(dados) >= limite:
            break
    return dados


def _artefatos_multifonte_da_resposta(mensagem: str, historico: list[dict[str, str]]) -> list[dict[str, Any]]:
    referencia = _resposta_anterior(historico)
    if not referencia:
        return []
    bloco_cti, bloco_web = _separar_blocos_multifonte(referencia)
    serie_cti = extrair_serie_numerica(bloco_cti)
    serie_web = extrair_serie_numerica(bloco_web)
    if len(serie_web) < 2:
        serie_web = _ranking_ordinal(bloco_web)

    graficos: list[dict[str, Any]] = []
    if len(serie_cti) >= 2:
        graficos.append(
            {
                "tipo": "GRAFICO",
                "formato": "BAR",
                "titulo": "Implementadoras em destaque no CTI — frequência histórica",
                "dados": serie_cti,
                "fonte_dados": "resposta_anterior:CTI",
                "proveniencia": "CTI",
                "metrica": "frequência de registros históricos",
                "auditavel": True,
            }
        )
    if len(serie_web) >= 2:
        ordinal = all(str(item.get("unidade") or "") == "posição" for item in serie_web)
        graficos.append(
            {
                "tipo": "GRAFICO",
                "formato": "RANKING" if ordinal else "BAR",
                "titulo": "Implementadoras em destaque no Brasil — ranking externo",
                "dados": serie_web,
                "fonte_dados": "resposta_anterior:WEB",
                "proveniencia": "WEB",
                "metrica": "posição no ranking externo (1 = maior destaque)" if ordinal else "métrica numérica explicitamente apresentada na resposta",
                "auditavel": True,
            }
        )
    return graficos


def gerar_resposta_agente(
    mensagem: str,
    historico: list[dict[str, str]] | None,
    usuario_id: str,
    tipo_usuario: str,
) -> tuple[str, dict[str, Any]]:
    resposta_texto, metadados = _ORIGINAL_GERAR_RESPOSTA(
        mensagem=mensagem,
        historico=historico,
        usuario_id=usuario_id,
        tipo_usuario=tipo_usuario,
    )
    metadados = dict(metadados or {})
    solicitados = detectar_intencao_artefato(mensagem)
    if solicitados:
        historico_atual = historico or []
        artefatos = construir_artefatos(
            mensagem=mensagem,
            resposta_texto=resposta_texto,
            historico=historico_atual,
            fontes=metadados.get("fontes") or [],
        )
        if "GRAFICO" in solicitados:
            graficos_multifonte = _artefatos_multifonte_da_resposta(mensagem, historico_atual)
            if graficos_multifonte:
                artefatos = [item for item in artefatos if item.get("tipo") != "GRAFICO"] + graficos_multifonte
        metadados["artefatos"] = artefatos
        metadados["ia009_artefatos_solicitados"] = sorted(solicitados)
        metadados["controle_artefatos"] = "geracao_deterministica_pos_sintese_sem_sql_livre"
        metadados["controle_artefatos_multifonte"] = "preserva_blocos_cti_web_sem_reconsulta"
        metadados["artefatos_auditaveis"] = True
    return resposta_texto, metadados


_agente.gerar_resposta_agente = gerar_resposta_agente
