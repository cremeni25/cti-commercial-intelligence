from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

from . import ia_comercial_sintese_crm as _sintese
from .ia_comercial_artefatos import construir_artefatos


_ORIGINAL_SINTETIZAR = _sintese.sintetizar_fatos_execucao

_RE_ITEM_METRICA = re.compile(
    r"^\s*(?:[-*•]\s*)?(?:\d+[.)-]?\s*)?(?P<label>[A-Za-zÀ-ÿ0-9 .&'()/\-]+?)\s*[—–-]\s*"
    r"(?P<valor>\d[\d\.\s]*(?:,\d+)?)\s*(?P<unidade>[A-Za-zÀ-ÿ% ]*?)"
    r"(?:\s*\((?P<detalhe>[^)]*)\))?\s*$"
)
_RE_TABELA = re.compile(
    r"^\s*\|\s*(?P<label>[^|]+?)\s*\|\s*(?P<valor>\d[\d\.\s]*(?:,\d+)?)\s*(?:\|.*)?$"
)


def _normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(ch for ch in bruto if not unicodedata.combining(ch)).casefold()


def _numero_ptbr(valor: str) -> float | None:
    texto = str(valor or "").strip().replace(" ", "")
    if not texto:
        return None
    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "." in texto:
        partes = texto.split(".")
        if len(partes) > 1 and all(len(p) == 3 for p in partes[1:]):
            texto = "".join(partes)
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _extrair_serie(texto: str, limite: int = 20) -> list[dict[str, Any]]:
    dados: list[dict[str, Any]] = []
    for linha in str(texto or "").splitlines():
        limpa = linha.strip()
        match = _RE_ITEM_METRICA.match(limpa)
        unidade = ""
        detalhe = ""
        if match:
            label = match.group("label").strip(" .:-")
            valor = _numero_ptbr(match.group("valor"))
            unidade = str(match.group("unidade") or "").strip()
            detalhe = str(match.group("detalhe") or "").strip()
        else:
            tabela = _RE_TABELA.match(limpa)
            if not tabela:
                continue
            label = tabela.group("label").strip(" .:-")
            if _normalizar(label) in {"implementadora", "item", "empresa"} or set(label) <= {"-", ":"}:
                continue
            valor = _numero_ptbr(tabela.group("valor"))
        if valor is None or not label or len(label) > 120:
            continue
        item: dict[str, Any] = {"label": label, "valor": valor, "unidade": unidade}
        if detalhe:
            item["detalhe"] = detalhe
        dados.append(item)
        if len(dados) >= limite:
            break
    return dados


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
        label = re.sub(r"\s*\([^)]*\)\s*$", "", label).strip().rstrip(".")
        if not label or re.search(r"\d", label):
            continue
        dados.append({"label": label, "valor": float(len(dados) + 1), "unidade": "posição"})
        if len(dados) >= limite:
            break
    return dados


def _separar_blocos(texto: str) -> tuple[str, str]:
    linhas = str(texto or "").splitlines()
    indice_web: int | None = None
    marcadores = (
        "externamente",
        "externo web",
        "ranking externo",
        "dados da web",
        "pesquisa na web",
        "complementando com dados da web",
        "em complemento",
        "separadamente",
    )
    for indice, linha in enumerate(linhas):
        normalizada = _normalizar(linha)
        if any(marcador in normalizada for marcador in marcadores):
            indice_web = indice
            break
    if indice_web is None:
        return str(texto or ""), ""
    return "\n".join(linhas[:indice_web]), "\n".join(linhas[indice_web:])


def _graficos_multifonte(texto: str) -> list[dict[str, Any]]:
    bloco_cti, bloco_web = _separar_blocos(texto)
    serie_cti = _extrair_serie(bloco_cti)
    serie_web = _extrair_serie(bloco_web)
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
                "fonte_dados": "snapshot_final:CTI",
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
                "formato": "BAR",
                "titulo": "Implementadoras em destaque no Brasil — fonte externa",
                "dados": serie_web,
                "fonte_dados": "snapshot_final:WEB",
                "proveniencia": "WEB",
                "metrica": "posição no ranking externo (1 = maior destaque)" if ordinal else "métrica numérica publicada na fonte externa",
                "auditavel": True,
            }
        )
    return graficos


def _snapshot_id(texto: str) -> str:
    return hashlib.sha256(str(texto or "").encode("utf-8")).hexdigest()[:24]


def sintetizar_fatos_execucao(
    pergunta_atual: str,
    metadados: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
):
    resposta_factual, metadados_sintese = _ORIGINAL_SINTETIZAR(
        pergunta_atual=pergunta_atual,
        metadados=metadados,
        usuario_id=usuario_id,
        tipo_usuario=tipo_usuario,
    )
    metadados_sintese = dict(metadados_sintese or {})
    contexto = dict((metadados or {}).get("ia009_contexto_pos_sintese") or {})
    solicitados = set(contexto.get("solicitados") or [])
    if not solicitados:
        return resposta_factual, metadados_sintese

    referencia = str(contexto.get("referencia_texto") or "").strip()
    texto_final = referencia or str(resposta_factual or "").strip()
    if not texto_final:
        return resposta_factual, metadados_sintese

    artefatos: list[dict[str, Any]] = []
    if "GRAFICO" in solicitados:
        artefatos.extend(_graficos_multifonte(texto_final))
        if not artefatos:
            artefatos = construir_artefatos(
                mensagem=pergunta_atual,
                resposta_texto=texto_final,
                historico=[],
                fontes=(metadados or {}).get("fontes") or [],
            )

    if "PDF" in solicitados or "RELATORIO" in solicitados:
        if not any(item.get("tipo") == "RELATORIO_PDF" for item in artefatos):
            artefatos.append(
                {
                    "tipo": "RELATORIO_PDF",
                    "titulo": "Relatório — IA Comercial CTI",
                    "fonte_dados": "snapshot_final",
                    "inclui_grafico": any(item.get("tipo") == "GRAFICO" and item.get("dados") for item in artefatos),
                    "fontes": (metadados or {}).get("fontes") or [],
                    "auditavel": True,
                }
            )

    snapshot = str(contexto.get("snapshot_evidencial_id") or "") or _snapshot_id(texto_final)
    metadados_sintese["artefatos"] = artefatos
    metadados_sintese["ia009_artefatos_solicitados"] = sorted(solicitados)
    metadados_sintese["snapshot_evidencial_id"] = snapshot
    metadados_sintese["controle_snapshot_evidencial"] = "congelado_pos_sintese_final"
    metadados_sintese["controle_fontes_snapshot"] = "uma_execucao_multifonte_um_snapshot"
    metadados_sintese["controle_artefatos_multifonte"] = "texto_grafico_pdf_mesmo_snapshot_final"
    metadados_sintese["artefatos_auditaveis"] = True
    return resposta_factual, metadados_sintese


_sintese.sintetizar_fatos_execucao = sintetizar_fatos_execucao
