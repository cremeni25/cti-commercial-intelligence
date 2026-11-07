"""Leitor somente-leitura da planilha NEGOCIAÇÕES (Viena SP).

Abas usadas:
- ``EM ANDAMENTO``: negociações abertas e histórico de fechamento, com status
  e data de follow-up;
- ``VENDAS``: vendas faturadas desde 2022 (mês, cliente, equipamento,
  quantidade, valores, instalação, vendedor).

Fica de fora o que não serve à inteligência comercial ou é pessoal: contato
(pessoa), anotações internas, comissões, NF, série e dados de pagamento de
comissão.
"""
from __future__ import annotations

import io
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from openpyxl import load_workbook

from parsers.historical_sales_funnel import normalize_representative

ABA_ANDAMENTO = "EM ANDAMENTO"
ABA_VENDAS = "VENDAS"
_LINHAS_VAZIAS_PARA_PARAR = 200


def _fold(valor: Any) -> str:
    texto = " ".join(str(valor or "").split()).upper()
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _texto(valor: Any) -> str | None:
    texto = " ".join(str(valor).split()) if valor is not None else ""
    return texto or None


def _numero(valor: Any) -> float | None:
    if isinstance(valor, bool) or valor in (None, ""):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _inteiro(valor: Any) -> int | None:
    numero = _numero(valor)
    return int(numero) if numero is not None and float(numero).is_integer() else None


def _data(valor: Any) -> str | None:
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, str):
        for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
            try:
                return datetime.strptime(valor.strip(), formato).date().isoformat()
            except ValueError:
                pass
    return None


def _vendedor(valor: Any) -> tuple[str | None, str | None]:
    original = _texto(valor)
    normalizado, _ = normalize_representative(original)
    return original, normalizado


def _aba(wb, nome: str):
    alvo = _fold(nome)
    for aba in wb.sheetnames:
        if _fold(aba) == alvo:
            return wb[aba]
    raise ValueError(f"Aba obrigatória ausente: {nome}")


def _linhas(ws, colunas: int) -> Iterable[tuple[int, tuple[Any, ...]]]:
    vazias = 0
    for numero, linha in enumerate(ws.iter_rows(min_row=2, max_col=colunas, values_only=True), start=2):
        if not any(v not in (None, "") for v in linha):
            vazias += 1
            if vazias >= _LINHAS_VAZIAS_PARA_PARAR:
                return
            continue
        vazias = 0
        yield numero, tuple(linha) + (None,) * (colunas - len(linha))


def _andamento(ws) -> list[dict[str, Any]]:
    registros = []
    for numero, c in _linhas(ws, 24):
        cliente = _texto(c[3])
        if not cliente:
            continue
        vendedor_original, vendedor = _vendedor(c[2])
        quantidade = _inteiro(c[8])
        valor_unitario = _numero(c[9])
        registros.append({
            "aba_origem": ABA_ANDAMENTO,
            "linha_origem": numero,
            "codigo_negociacao": _texto(c[0]),
            "data": _data(c[1]),
            "vendedor_original": vendedor_original,
            "vendedor": vendedor,
            "cliente": cliente,
            "cnpj": _texto(c[4]),
            "linha_equipamento": _texto(c[6]),
            "equipamento": _texto(c[7]),
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "valor_instalacao": _numero(c[10]),
            "valor_total": _numero(c[11]),
            "condicao_pagamento": _texto(c[12]),
            "instalacao": _texto(c[14]),
            "canal_venda": _texto(c[15]),
            "indicacao": _texto(c[16]),
            "follow_up": _data(c[17]),
            "status": _texto(c[18]),
            "caso_sc": _texto(c[20]),
            "baixa": _texto(c[23]),
        })
    return registros


def _vendas(ws) -> list[dict[str, Any]]:
    registros = []
    for numero, c in _linhas(ws, 23):
        cliente = _texto(c[3])
        if not cliente:
            continue
        vendedor_original, vendedor = _vendedor(c[22])
        quantidade = _inteiro(c[6])
        valor_unitario = _numero(c[7])
        registros.append({
            "aba_origem": ABA_VENDAS,
            "linha_origem": numero,
            "mes": _data(c[0]),
            "pendencia": _texto(c[1]),
            "codigo_negociacao": _texto(c[2]),
            "cliente": cliente,
            "linha_equipamento": _texto(c[4]),
            "equipamento": _texto(c[5]),
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "valor_total_equipamento": round(valor_unitario * quantidade, 2) if valor_unitario is not None and quantidade is not None else None,
            "valor_instalacao": _numero(c[8]),
            "condicao_pagamento": _texto(c[9]),
            "canal_venda": _texto(c[10]),
            "data_emissao": _data(c[12]),
            "data_instalacao": _data(c[16]),
            "instalador": _texto(c[17]),
            "vendedor_original": vendedor_original,
            "vendedor": vendedor,
        })
    return registros


def ler_negociacoes(origem: str | Path | bytes) -> dict[str, list[dict[str, Any]]]:
    arquivo = io.BytesIO(origem) if isinstance(origem, (bytes, bytearray)) else origem
    wb = load_workbook(arquivo, data_only=True, read_only=True)
    try:
        return {"negociacoes_andamento": _andamento(_aba(wb, ABA_ANDAMENTO)), "vendas_realizadas": _vendas(_aba(wb, ABA_VENDAS))}
    finally:
        wb.close()
