"""Planilhas comerciais vivas (funil de vendas e NEGOCIAÇÕES) para o CTI.

Enquanto a leitura automática do SharePoint não é autorizada, o Master envia
as planilhas pelo CTI (web ou app). O backend lê, normaliza e guarda o pacote
no cofre PRIVADO do agente (``planilhas/pacote-comercial.json.gz``); nenhum
dado de cliente passa pelo repositório público. A mesma ``montar_pacote``
servirá à leitura automática semanal.

Compatível com um pacote cifrado em ``data/planilhas_cifradas/`` (usado só se
o cofre ainda não tiver carga).

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
from time import monotonic
from typing import Any

from parsers.historical_sales_funnel import parse_workbook
from parsers.planilha_negociacoes import ler_negociacoes
from services.anfir_market_scope import filtrar_mercado_real_viena

DIRETORIO = Path(__file__).resolve().parents[1] / "data" / "planilhas_cifradas"
ARQUIVO_PACOTE = DIRETORIO / "pacote-comercial.json"
ROTULO = "pacote-comercial"
VERSAO_PACOTE = 1
COFRE_PACOTE = "planilhas/pacote-comercial.json.gz"
VALIDADE_CACHE_S = 600  # outras instâncias do backend enxergam a carga nova em até 10 min

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


def _ler_partes(funil: tuple[str, bytes] | None, negociacoes: tuple[str, bytes] | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dados: dict[str, Any] = {}
    arquivos = []
    if funil:
        dados["funil_vendas_atual"] = _ler_funil(funil[1], funil[0])
        arquivos.append({"nome": funil[0], "sha256": sha256(funil[1]).hexdigest(), "tipo": "FUNIL_VENDAS"})
    if negociacoes:
        dados.update(ler_negociacoes(negociacoes[1]))
        arquivos.append({"nome": negociacoes[0], "sha256": sha256(negociacoes[1]).hexdigest(), "tipo": "NEGOCIACOES"})
    return dados, arquivos


def _pacote(dados: dict[str, Any], arquivos: list[dict[str, Any]], origem: str) -> dict[str, Any]:
    return {
        "versao": VERSAO_PACOTE,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "origem": origem,
        "arquivos": arquivos,
        "totais": {chave: len(valor) for chave, valor in dados.items()},
        "dados": dados,
    }


def montar_pacote(funil: tuple[str, bytes], negociacoes: tuple[str, bytes], origem: str) -> dict[str, Any]:
    """Lê as duas planilhas e devolve o pacote normalizado."""
    dados, arquivos = _ler_partes(funil, negociacoes)
    return _pacote(dados, arquivos, origem)


def compactar(pacote: dict[str, Any]) -> bytes:
    return gzip.compress(json.dumps(pacote, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8"), mtime=0)


def _de_bytes(bruto: bytes) -> dict[str, Any]:
    pacote = json.loads(gzip.decompress(bruto).decode("utf-8"))
    if not isinstance(pacote, dict) or pacote.get("versao") != VERSAO_PACOTE or not isinstance(pacote.get("dados"), dict):
        raise ValueError("Pacote comercial em formato desconhecido.")
    return pacote


def _abrir_pacote() -> dict[str, Any] | None:
    from services import cofre_agente

    bruto = cofre_agente.ler_binario(COFRE_PACOTE)
    if bruto:
        return _de_bytes(bruto)
    if not ARQUIVO_PACOTE.exists():
        return None
    from services import cofre_cifrado

    envelope = cofre_cifrado.ler_envelope(str(ARQUIVO_PACOTE))
    if envelope.get("rotulo") != ROTULO:
        raise cofre_cifrado.EnvelopeInvalido("Pacote com rótulo inesperado.")
    return _de_bytes(cofre_cifrado.abrir(envelope))


def carregar_pacote() -> dict[str, Any] | None:
    """Pacote aberto (em memória). Falha de abertura não derruba quem consulta."""
    with _trava:
        if "pacote" in _cache and monotonic() - _cache.get("lido_em", 0) < VALIDADE_CACHE_S:
            return _cache["pacote"]
        try:
            pacote = _abrir_pacote()
            _cache["erro"] = None
        except Exception as erro:  # cofre fora do ar, chave trocada, arquivo corrompido
            _cache["erro"] = str(erro)
            return _cache.get("pacote")
        _cache["pacote"] = pacote
        _cache["lido_em"] = monotonic()
        return pacote


def limpar_cache() -> None:
    with _trava:
        _cache.clear()


def atualizar_pacote(funil: tuple[str, bytes] | None, negociacoes: tuple[str, bytes] | None, usuario_id: str) -> dict[str, Any]:
    """Carga enviada pelo Master: lê o que veio e mantém do pacote atual o que não veio."""
    from services import cofre_agente

    if not funil and not negociacoes:
        raise ValueError("Envie ao menos uma planilha.")
    novos, arquivos = _ler_partes(funil, negociacoes)
    atual = carregar_pacote() or {}
    dados = dict(atual.get("dados") or {})
    dados.update(novos)
    tipos_novos = {a["tipo"] for a in arquivos}
    enviado_em = datetime.now(timezone.utc).isoformat()
    for arquivo in arquivos:
        arquivo.update({"enviado_em": enviado_em, "enviado_por": usuario_id})
    arquivos += [a for a in atual.get("arquivos", []) if a.get("tipo") not in tipos_novos]
    pacote = _pacote(dados, arquivos, "ENVIO_PELO_CTI")
    cofre_agente.gravar_binario(COFRE_PACOTE, compactar(pacote), "application/gzip")
    with _trava:
        _cache.update({"pacote": pacote, "lido_em": monotonic(), "erro": None})
    return resumo()


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
        return {"disponivel": False, "erro": _cache.get("erro")}
    vendas = registros("vendas_realizadas")
    andamento = registros("negociacoes_andamento")
    funil = registros("funil_vendas_atual")
    return {
        "disponivel": True,
        "gerado_em": pacote.get("gerado_em"),
        "origem": pacote.get("origem"),
        "arquivos": [{"nome": a.get("nome"), "tipo": a.get("tipo"), "enviado_em": a.get("enviado_em")} for a in pacote.get("arquivos", [])],
        "totais": {"funil_vendas_atual": len(funil), "negociacoes_andamento": len(andamento), "vendas_realizadas": len(vendas)},
        "funil_por_status": _contar(funil, "status"),
        "vendas_por_ano": dict(sorted(Counter(str(v.get("mes") or "")[:4] or "SEM DATA" for v in vendas).items())),
        "vendas_por_vendedor": _contar(vendas, "vendedor"),
        "equipamentos_mais_vendidos": _contar(vendas, "equipamento"),
    }
