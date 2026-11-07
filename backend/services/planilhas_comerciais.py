"""Planilhas comerciais vivas (funil de vendas e NEGOCIAÇÕES) para o CTI.

Enquanto a leitura automática do SharePoint não é autorizada, a carga chega
como um único pacote CIFRADO em ``data/planilhas_cifradas/pacote-comercial.json``
(repositório público: o conteúdo só abre no backend, com a chave do cofre).
A mesma função ``montar_pacote`` servirá à leitura automática semanal.

O pacote é somente leitura: alimenta a IA Comercial e as leituras de gestão,
sem criar nem alterar clientes, oportunidades ou pedidos do CRM.
"""
from __future__ import annotations

import gzip
import json
import tempfile
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any

from parsers.historical_sales_funnel import parse_workbook
from parsers.planilha_negociacoes import ler_negociacoes
from services.anfir_market_scope import filtrar_mercado_real_viena

DIRETORIO = Path(__file__).resolve().parents[1] / "data" / "planilhas_cifradas"
ARQUIVO_PACOTE = DIRETORIO / "pacote-comercial.json"
ROTULO = "pacote-comercial"
VERSAO_PACOTE = 1

_trava = Lock()
_cache: dict[str, Any] = {}


def _registro_funil(registro) -> dict[str, Any]:
    item = registro.as_dict()
    data = item.get("data_normalizada")
    return {
        "origem_semantica": "FUNIL_VENDAS_ATUAL",
        "aba_origem": item["aba_origem"],
        "linha_origem": item["linha_origem"],
        "representante_original": item["representante_original"],
        "representante_atual": item["representante_normalizado"],
        "data": data,
        "ano": int(data[:4]) if data else None,
        "cliente": item["cliente_normalizado"] or item["cliente_original"],
        "equipamento": item["equipamento_original"],
        "quantidade": item["quantidade"],
        "valor_unitario": float(item["valor_unitario"]) if item["valor_unitario"] is not None else None,
        "valor_total": float(item["valor_total"]) if item["valor_total"] is not None else None,
        "previsao": item["previsao_original"],
        "probabilidade": float(item["probabilidade_normalizada"]) if item["probabilidade_normalizada"] is not None else None,
        "status": item["status_normalizado"] or "INDETERMINADO",
        "motivo_perda": item["motivo_perda_normalizado"],
        "observacao": item["observacao_original"],
        "canal_venda": item["canal_venda"],
        "implementadora": item["implementadora_normalizada"] or item["implementadora_original"],
        "flags_validacao": item["flags_validacao"],
    }


def _ler_funil(conteudo: bytes, nome: str) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / Path(nome).name
        caminho.write_bytes(conteudo)
        return [_registro_funil(r) for r in parse_workbook(caminho)]


def montar_pacote(funil: tuple[str, bytes], negociacoes: tuple[str, bytes], origem: str) -> dict[str, Any]:
    """Lê as duas planilhas e devolve o pacote normalizado (sem cifrar)."""
    nome_funil, bytes_funil = funil
    nome_neg, bytes_neg = negociacoes
    dados = {"funil_vendas_atual": _ler_funil(bytes_funil, nome_funil), **ler_negociacoes(bytes_neg)}
    return {
        "versao": VERSAO_PACOTE,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "origem": origem,
        "arquivos": [
            {"nome": nome_funil, "sha256": sha256(bytes_funil).hexdigest(), "tipo": "FUNIL_VENDAS"},
            {"nome": nome_neg, "sha256": sha256(bytes_neg).hexdigest(), "tipo": "NEGOCIACOES"},
        ],
        "totais": {chave: len(valor) for chave, valor in dados.items()},
        "dados": dados,
    }


def compactar(pacote: dict[str, Any]) -> bytes:
    return gzip.compress(json.dumps(pacote, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8"), mtime=0)


def _abrir_pacote() -> dict[str, Any] | None:
    if not ARQUIVO_PACOTE.exists():
        return None
    from services import cofre_cifrado

    envelope = cofre_cifrado.ler_envelope(str(ARQUIVO_PACOTE))
    if envelope.get("rotulo") != ROTULO:
        raise cofre_cifrado.EnvelopeInvalido("Pacote com rótulo inesperado.")
    pacote = json.loads(gzip.decompress(cofre_cifrado.abrir(envelope)).decode("utf-8"))
    if not isinstance(pacote, dict) or pacote.get("versao") != VERSAO_PACOTE or not isinstance(pacote.get("dados"), dict):
        raise ValueError("Pacote comercial em formato desconhecido.")
    return pacote


def carregar_pacote() -> dict[str, Any] | None:
    """Pacote aberto (em memória). Falha de abertura não derruba quem consulta."""
    with _trava:
        if "pacote" in _cache:
            return _cache["pacote"]
        try:
            pacote = _abrir_pacote()
            _cache["erro"] = None
        except Exception as erro:  # cofre fora do ar, chave trocada, arquivo corrompido
            _cache["erro"] = str(erro)
            return None
        _cache["pacote"] = pacote
        return pacote


def limpar_cache() -> None:
    with _trava:
        _cache.clear()


def registros(fonte: str) -> list[dict[str, Any]]:
    pacote = carregar_pacote() or {}
    linhas = list((pacote.get("dados") or {}).get(fonte) or [])
    if fonte == "funil_vendas_atual":
        return filtrar_mercado_real_viena(linhas)
    return linhas


def _contar(linhas: list[dict[str, Any]], campo: str, limite: int = 10) -> dict[str, int]:
    return dict(Counter(str(item.get(campo) or "NÃO INFORMADO") for item in linhas).most_common(limite))


def resumo() -> dict[str, Any]:
    pacote = carregar_pacote()
    if not pacote:
        return {"disponivel": False, "erro": _cache.get("erro"), "arquivo_presente": ARQUIVO_PACOTE.exists()}
    vendas = registros("vendas_realizadas")
    andamento = registros("negociacoes_andamento")
    funil = registros("funil_vendas_atual")
    return {
        "disponivel": True,
        "gerado_em": pacote.get("gerado_em"),
        "origem": pacote.get("origem"),
        "arquivos": [{"nome": a.get("nome"), "tipo": a.get("tipo")} for a in pacote.get("arquivos", [])],
        "totais": {"funil_vendas_atual": len(funil), "negociacoes_andamento": len(andamento), "vendas_realizadas": len(vendas)},
        "funil_por_status": _contar(funil, "status"),
        "vendas_por_ano": dict(sorted(Counter(str(v.get("mes") or "")[:4] or "SEM DATA" for v in vendas).items())),
        "vendas_por_vendedor": _contar(vendas, "vendedor"),
        "equipamentos_mais_vendidos": _contar(vendas, "equipamento"),
    }
