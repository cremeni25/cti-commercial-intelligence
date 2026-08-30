from __future__ import annotations

import json
import math
import unicodedata
from collections import Counter
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException

from services.crm_live_projection import carregar_oportunidades_enriquecidas, familias_registro
from services.historical_commercial_source import carregar_historico_comercial
from services.anfir_workbook_contract import _ddd_workbook
from services.anfir_workbook_semantics import (
    categoria_workbook_2026,
    causa_workbook_2026,
    extrair_observacao_workbook,
    temas_workbook_2026,
)
from services.operational_filters import data_registro
from routers.strategic_layers_router import (
    _anfir,
    _data_no_intervalo,
    _familia_historico,
    _familia_registro_anfir,
)

router = APIRouter(prefix="/estrategia", tags=["Estratégia CTI - Drill-down"])

CAMPOS: dict[str, dict[str, tuple[str, ...]]] = {
    "anfir": {
        "estado": ("estado", "uf"),
        "municipio": ("cidade", "municipio"),
        "ddd": ("ddd",),
        "implementadora": ("implementadora", "implementador"),
        "empresa": ("cliente", "empresa", "transportadora"),
        "equipamento": ("modelo", "linha", "produto"),
        # Campos semânticos do workbook 2026. São filtrados pelas mesmas regras
        # usadas na consolidação do Dashboard, não por texto bruto.
        "categoria": (),
        "causa": (),
        "mes": (),
        "trimestre": (),
        "tema": (),
        "observacao": (),
    },
    "historico": {
        "aba": ("aba_origem",),
        "ano": ("ano",),
        "canal": ("canal_venda",),
        "representante": ("representante_atual",),
        "status": ("status",),
        "equipamento": ("equipamento",),
        "implementadora": ("implementadora",),
        "motivo_perda": ("motivo_perda",),
        "empresa": ("cliente",),
    },
    "crm": {
        "estado": ("estado",),
        "municipio": ("municipio",),
        "ddd": ("ddd",),
        "equipamento": ("equipamentos", "equipamento", "linha_equipamentos"),
        "status": ("status",),
        "empresa": ("cliente_nome", "cliente", "empresa"),
    },
}

COLUNAS = {
    "anfir": ["cliente", "empresa", "transportadora", "estado", "cidade", "municipio", "ddd", "implementadora", "modelo", "linha", "produto", "valor", "data", "created_at", "observacao"],
    "historico": ["aba_origem", "linha_origem", "data", "ano", "cliente", "equipamento", "quantidade", "valor_unitario", "valor_total", "representante_original", "representante_atual", "status", "motivo_perda", "canal_venda", "implementadora", "previsao", "probabilidade", "observacao"],
    "crm": ["id", "titulo", "cliente_nome", "status", "equipamentos", "linhas_equipamentos", "quantidade_total", "valor_estimado", "estado", "municipio", "ddd", "data_fechamento_prevista", "created_at"],
}


def _fold(valor: Any) -> str:
    texto = str(valor or "").strip().upper()
    return "".join(ch for ch in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(ch))


def _valor_campo(registro: dict[str, Any], candidatos: tuple[str, ...]) -> Any:
    for chave in candidatos:
        valor = registro.get(chave)
        if valor not in (None, "", []):
            return valor
    return None


def _corresponde(registro: dict[str, Any], candidatos: tuple[str, ...], valor: str) -> bool:
    alvo = _fold(valor)
    for chave in candidatos:
        atual = registro.get(chave)
        if isinstance(atual, list):
            if any(_fold(item) == alvo for item in atual):
                return True
            continue
        if atual not in (None, "") and _fold(atual) == alvo:
            return True
    return False


def _buscar(registros: list[dict[str, Any]], busca: str | None) -> list[dict[str, Any]]:
    if not busca:
        return registros
    alvo = _fold(busca)
    return [item for item in registros if alvo in _fold(json.dumps(item, ensure_ascii=False, default=str))]


def _ordenar(registros: list[dict[str, Any]], campo: str | None, direcao: str) -> list[dict[str, Any]]:
    if not campo:
        return registros
    reverso = str(direcao or "asc").lower() == "desc"
    return sorted(registros, key=lambda item: (_fold(item.get(campo)) == "", _fold(item.get(campo))), reverse=reverso)


def _projetar(registro: dict[str, Any], camada: str) -> dict[str, Any]:
    chaves = COLUNAS[camada]
    projetado = {chave: registro.get(chave) for chave in chaves if registro.get(chave) not in (None, "", [], {})}
    if camada == "anfir":
        observacao = extrair_observacao_workbook(registro)
        projetado["categoria_workbook"] = categoria_workbook_2026(registro)
        projetado["causa_workbook"] = causa_workbook_2026(registro)
        projetado["ddd_workbook"] = _ddd_workbook(registro)
        temas = temas_workbook_2026(registro)
        if temas:
            projetado["temas_workbook"] = temas
        if observacao:
            projetado["observacao"] = observacao
    if not projetado:
        projetado = {chave: valor for chave, valor in registro.items() if valor not in (None, "", [], {})}
    return projetado


def _ranking_historico(registros: list[dict[str, Any]], chave: str, limite: int | None = None) -> list[dict[str, Any]]:
    contagem: Counter[str] = Counter()
    rotulos: dict[str, str] = {}
    for item in registros:
        valor = item.get(chave)
        if valor in (None, ""):
            continue
        normalizado = _fold(valor)
        if not normalizado:
            continue
        contagem[normalizado] += 1
        if normalizado not in rotulos:
            rotulos[normalizado] = str(valor).strip().upper()
    pares = sorted(contagem.items(), key=lambda par: (-par[1], rotulos[par[0]]))
    if limite is not None:
        pares = pares[:limite]
    return [{"nome": rotulos[chave_normalizada], "quantidade_registros": quantidade} for chave_normalizada, quantidade in pares]


def _numero(valor: Any) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _filtrar_anfir_semantico(registros: list[dict[str, Any]], campo: str, valor: str) -> list[dict[str, Any]]:
    alvo = str(valor or "").strip()
    if campo == "categoria":
        return [item for item in registros if categoria_workbook_2026(item) == alvo]
    if campo == "causa":
        return [item for item in registros if causa_workbook_2026(item) == alvo]
    if campo == "mes":
        return [item for item in registros if (d := data_registro(item)) and d.strftime("%Y-%m") == alvo]
    if campo == "trimestre":
        try:
            ano_texto, trimestre_texto = alvo.upper().split("-Q", 1)
            ano, trimestre = int(ano_texto), int(trimestre_texto)
        except (TypeError, ValueError):
            return []
        return [item for item in registros if (d := data_registro(item)) and d.year == ano and ((d.month - 1) // 3 + 1) == trimestre]
    if campo == "tema":
        return [item for item in registros if alvo in temas_workbook_2026(item)]
    if campo == "observacao":
        if alvo == "COM_OBSERVACAO":
            return [item for item in registros if extrair_observacao_workbook(item)]
        if alvo == "SEM_OBSERVACAO":
            return [item for item in registros if not extrair_observacao_workbook(item)]
        return []
    if campo == "ddd":
        return [item for item in registros if _ddd_workbook(item) == alvo]
    return [item for item in registros if _corresponde(item, CAMPOS["anfir"][campo], alvo)]


@router.get("/detalhamento/resumo-historico")
def resumo_historico():
    registros = list(carregar_historico_comercial())
    return {
        "total_registros": len(registros),
        "total_unidades": int(sum(_numero(item.get("quantidade")) for item in registros)),
        "valor_nominal": round(sum(_numero(item.get("valor_total")) for item in registros), 2),
        "abas": _ranking_historico(registros, "aba_origem"),
        "anos": _ranking_historico(registros, "ano"),
        "canais": _ranking_historico(registros, "canal_venda"),
        "representantes": _ranking_historico(registros, "representante_atual"),
        "status": _ranking_historico(registros, "status"),
        "equipamentos": _ranking_historico(registros, "equipamento", 20),
        "implementadoras": _ranking_historico(registros, "implementadora", 20),
        "motivos_perda": _ranking_historico(registros, "motivo_perda", 20),
    }


@router.get("/detalhamento")
def detalhamento_indicador(
    camada: str,
    campo: str | None = None,
    valor: str | None = None,
    familia: str | None = None,
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    busca: str | None = None,
    ordenar: str | None = None,
    direcao: str = "asc",
    pagina: int = 1,
    limite: int = 50,
):
    camada = camada.strip().lower()
    if camada not in CAMPOS:
        raise HTTPException(status_code=422, detail="Camada de detalhamento inválida.")
    if campo and campo not in CAMPOS[camada] and campo != "familia":
        raise HTTPException(status_code=422, detail="Campo de detalhamento não suportado para esta camada.")

    if camada == "anfir":
        registros, inicio_efetivo, fim_efetivo = _anfir(contexto, periodo, uf, ddd, inicio, fim)
        if familia:
            registros = [item for item in registros if _familia_registro_anfir(item) == familia]
    elif camada == "historico":
        from services.operational_filters import resolver_periodo
        inicio_efetivo, fim_efetivo = resolver_periodo(periodo, inicio, fim)
        registros = [item for item in carregar_historico_comercial() if _data_no_intervalo(item.get("data"), inicio_efetivo, fim_efetivo)]
        if familia:
            registros = [item for item in registros if _familia_historico(item) == familia]
    else:
        inicio_efetivo, fim_efetivo = inicio, fim
        fechados = {"GANHO", "PERDIDO", "CANCELADO", "CANCELADA", "CONCLUIDO", "CONCLUIDA"}
        registros = [item for item in carregar_oportunidades_enriquecidas() if str(item.get("status") or "").upper() not in fechados]
        if familia:
            registros = [item for item in registros if familia in familias_registro(item)]

    if campo == "familia" and valor:
        familia_alvo = valor
        if camada == "anfir":
            registros = [item for item in registros if _familia_registro_anfir(item) == familia_alvo]
        elif camada == "historico":
            registros = [item for item in registros if _familia_historico(item) == familia_alvo]
        else:
            registros = [item for item in registros if familia_alvo in familias_registro(item)]
    elif campo and valor:
        if camada == "anfir":
            registros = _filtrar_anfir_semantico(list(registros), campo, valor)
        else:
            registros = [item for item in registros if _corresponde(item, CAMPOS[camada][campo], valor)]

    registros = _buscar(list(registros), busca)
    registros = _ordenar(registros, ordenar, direcao)

    pagina = max(1, pagina)
    limite = max(10, min(limite, 100))
    total = len(registros)
    paginas = max(1, math.ceil(total / limite)) if total else 1
    if pagina > paginas:
        pagina = paginas
    inicio_idx = (pagina - 1) * limite
    fim_idx = inicio_idx + limite

    return {
        "camada": camada,
        "campo": campo,
        "valor": valor,
        "familia": familia,
        "total_registros": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": paginas,
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "uf": uf,
            "ddd": ddd,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
        },
        "registros": [_projetar(item, camada) for item in registros[inicio_idx:fim_idx]],
    }
