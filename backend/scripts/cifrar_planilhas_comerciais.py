"""Prepara a carga cifrada do funil e das NEGOCIAÇÕES para o repositório público.

Uso (as planilhas originais ficam FORA do repositório):
    python scripts/cifrar_planilhas_comerciais.py --funil FUNIL.xlsx --negociacoes NEGOCIACOES.xlsx \
        --chave-url https://cti-backend-5ugf.onrender.com/ingestao-cifrada/chave-publica

Lê as planilhas com os mesmos leitores do backend, cifra o pacote com a chave
PÚBLICA do backend e grava data/planilhas_cifradas/pacote-comercial.json.
Nada legível das planilhas é gravado no repositório.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.cofre_cifrado import cifrar  # noqa: E402
from services.planilhas_comerciais import ARQUIVO_PACOTE, ROTULO, compactar, montar_pacote  # noqa: E402


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--funil", required=True)
    args.add_argument("--negociacoes", required=True)
    args.add_argument("--chave-url", required=True)
    args.add_argument("--origem", default="CARGA_ENVIADA_PELA_GESTAO")
    opcoes = args.parse_args()
    with urllib.request.urlopen(opcoes.chave_url, timeout=90) as resposta:
        chave = json.load(resposta)["chave_publica"]
    pacote = montar_pacote(
        ("funil de vendas 2026.xlsx", Path(opcoes.funil).read_bytes()),
        ("NEGOCIAÇÕES.xlsx", Path(opcoes.negociacoes).read_bytes()),
        opcoes.origem,
    )
    envelope = cifrar(compactar(pacote), chave, ROTULO)
    ARQUIVO_PACOTE.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_PACOTE.write_text(json.dumps(envelope, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"arquivo": str(ARQUIVO_PACOTE), "totais": pacote["totais"], "bytes": ARQUIVO_PACOTE.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
