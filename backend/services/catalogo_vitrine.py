"""Vitrine do catálogo para a equipe comercial.

Junta, em uma leitura só, o catálogo comercial oficial (equipamentos e preço
de tabela vigente) e os materiais de divulgação (catálogos, fichas técnicas,
vídeos — por exemplo os links publicados no Linktree da operação).

- Preço de tabela só é devolvido a quem já pode ver/emitir propostas.
- Materiais vivem em ``data/catalogo_materiais.json`` (versionado, revisável
  em PR, sem migração de banco). Cada material se liga a uma linha, a
  equipamentos específicos ou a termos do nome comercial.
- Se o catálogo comercial não puder ser lido, a vitrine cai para o catálogo
  oficial de linhas/modelos, sem preços — a equipe nunca fica sem consulta.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

ARQUIVO_MATERIAIS = Path(__file__).resolve().parents[1] / "data" / "catalogo_materiais.json"
ARQUIVO_TABELA_APLICACAO = Path(__file__).resolve().parents[1] / "data" / "tabela_aplicacao.json"
PASTA_MATERIAIS_INTERNOS = "materiais"
INDICE_MATERIAIS_INTERNOS = "materiais/indice.json"
LINHAS = (
    ("TRAILER", "Trailer", "TR", "Semirreboques e carretas frigoríficas"),
    ("DIESEL TRUCK", "Diesel Truck", "DT", "Caminhões com motor diesel próprio"),
    ("DIRECT DRIVE", "Direct Drive", "DD", "Veículos leves e médios acionados pelo motor"),
)
LINHA_POR_SIGLA = {sigla: codigo for codigo, _, sigla, _ in LINHAS}
TIPOS_MATERIAL = {"catalogo", "ficha_tecnica", "video", "manual", "apresentacao", "outro"}


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", texto).strip().casefold()


def _linha_canonica(valor: Any) -> str:
    bruto = str(valor or "").strip().upper().replace("_", " ")
    return LINHA_POR_SIGLA.get(bruto, bruto)


@lru_cache(maxsize=1)
def _materiais_brutos(caminho: str = str(ARQUIVO_MATERIAIS)) -> dict[str, Any]:
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"linktree_url": None, "materiais": []}


@lru_cache(maxsize=1)
def tabela_aplicacao() -> dict[str, Any] | None:
    """Tabela de aplicação (equipamento x tamanho do baú x temperatura mínima)."""
    try:
        dados = json.loads(ARQUIVO_TABELA_APLICACAO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    tamanhos = dados.get("tamanhos") or []
    equipamentos = [e for e in dados.get("equipamentos") or [] if len(e.get("temperaturas") or []) == len(tamanhos)]
    return {**dados, "equipamentos": equipamentos} if tamanhos and equipamentos else None


def materiais_internos() -> list[dict[str, Any]]:
    """Materiais privados (ex.: PDF original da tabela) com link temporário de 1 h."""
    from services import cofre_agente as cofre

    try:
        indice = cofre.ler(INDICE_MATERIAIS_INTERNOS, []) or []
    except Exception:
        return []
    saida = []
    for item in indice:
        if not isinstance(item, dict) or not item.get("arquivo"):
            continue
        url = cofre.url_assinada(f"{PASTA_MATERIAIS_INTERNOS}/{item['arquivo']}")
        if url:
            saida.append({"titulo": item.get("titulo") or item["arquivo"], "url": url, "tipo": item.get("tipo") or "catalogo", "enviado_em": item.get("enviado_em")})
    return saida


def materiais_validos(conteudo: dict[str, Any]) -> list[dict[str, Any]]:
    validos = []
    for item in conteudo.get("materiais") or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        titulo = str(item.get("titulo") or "").strip()
        if not titulo or not url.startswith("https://"):
            continue  # somente links seguros e identificados
        validos.append({
            "titulo": titulo,
            "url": url,
            "tipo": item.get("tipo") if item.get("tipo") in TIPOS_MATERIAL else "outro",
            "linhas": [_linha_canonica(l) for l in item.get("linhas") or []],
            "equipamentos": [str(c).strip().upper() for c in item.get("equipamentos") or []],
            "termos": [_fold(t) for t in item.get("termos") or [] if _fold(t)],
        })
    return validos


def _publico(material: dict[str, Any]) -> dict[str, Any]:
    return {"titulo": material["titulo"], "url": material["url"], "tipo": material["tipo"]}


def _materiais_do_equipamento(equipamento: dict[str, Any], materiais: list[dict[str, Any]]) -> list[dict[str, Any]]:
    codigo = str(equipamento.get("codigo") or "").upper()
    nome = _fold(f"{equipamento.get('nome_comercial') or ''} {equipamento.get('modelo_base') or ''}")
    return [
        _publico(m) for m in materiais
        if codigo in m["equipamentos"] or any(t in nome for t in m["termos"])
    ]


def _preco_vigente(precos: list[dict[str, Any]], codigo: str, hoje: date) -> dict[str, Any] | None:
    candidatos = [
        p for p in precos
        if str(p.get("equipamento_codigo")) == codigo
        and str(p.get("vigencia_inicio") or "")[:10] <= hoje.isoformat()
        and (not p.get("vigencia_fim") or str(p.get("vigencia_fim"))[:10] >= hoje.isoformat())
    ]
    if not candidatos:
        return None
    atual = max(candidatos, key=lambda p: str(p.get("vigencia_inicio") or ""))
    return {"valor": float(atual.get("preco_cheio") or 0), "moeda": atual.get("moeda") or "BRL", "tabela": atual.get("tabela_codigo"), "vigencia_inicio": str(atual.get("vigencia_inicio") or "")[:10]}


def _ler_catalogo_comercial() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from core.supabase_client import supabase

    equipamentos = supabase.table("cti_catalogo_equipamentos").select("*").eq("ativo", True).execute().data or []
    precos = supabase.table("cti_tabela_precos").select("*").eq("ativo", True).execute().data or []
    return equipamentos, precos


def _equipamentos_do_catalogo_oficial() -> list[dict[str, Any]]:
    from services.product_catalog_service import listar_catalogo

    nomes = {"TR": "TRAILER", "DT": "DIESEL TRUCK", "DD": "DIRECT DRIVE"}
    saida = []
    for ordem, linha in enumerate(listar_catalogo().get("lines") or []):
        for indice, modelo in enumerate(linha.get("models") or []):
            if modelo.get("active") is False:
                continue
            nome = str(modelo.get("canonical_name") or "").strip()
            saida.append({"codigo": re.sub(r"[^A-Z0-9]+", "-", nome.upper()).strip("-"), "linha_produto": nomes.get(str(linha.get("code")).upper(), str(linha.get("name") or "").upper()),
                          "modelo_base": nome, "nome_comercial": nome, "configuracao": "PADRAO", "ordem": ordem * 100 + indice})
    return saida


def montar_vitrine(*, equipamentos: list[dict[str, Any]], precos: list[dict[str, Any]], materiais_conteudo: dict[str, Any],
                   ver_precos: bool, hoje: date, fonte: str) -> dict[str, Any]:
    materiais = materiais_validos(materiais_conteudo)
    vinculados: set[str] = set()  # URLs de materiais de modelo que encontraram um equipamento
    linhas_saida = []
    for codigo_linha, nome, sigla, descricao in LINHAS:
        da_linha = sorted(
            [e for e in equipamentos if _linha_canonica(e.get("linha_produto")) == codigo_linha],
            key=lambda e: (int(e.get("ordem") or 0), str(e.get("nome_comercial") or "")),
        )
        itens = []
        for equipamento in da_linha:
            codigo = str(equipamento.get("codigo") or "")
            descricao_tecnica = equipamento.get("descricao_tecnica") if isinstance(equipamento.get("descricao_tecnica"), dict) else {}
            itens.append({
                "codigo": codigo,
                "nome_comercial": equipamento.get("nome_comercial") or equipamento.get("modelo_base") or codigo,
                "modelo_base": equipamento.get("modelo_base"),
                "configuracao": equipamento.get("configuracao") or "PADRAO",
                "compressor": equipamento.get("compressor"),
                "possui_eletrico": bool(equipamento.get("possui_eletrico")),
                "descricao_tecnica": {str(k): v for k, v in descricao_tecnica.items() if v not in (None, "", [], {})},
                "preco_vigente": _preco_vigente(precos, codigo, hoje) if ver_precos else None,
                "materiais": _materiais_do_equipamento(equipamento, materiais),
            })
            vinculados.update(m["url"] for m in itens[-1]["materiais"])
        linhas_saida.append({
            "codigo": codigo_linha, "nome": nome, "sigla": sigla, "descricao": descricao,
            "equipamentos": itens,
            # Material da linha, ou material de modelo que não achou o modelo no
            # catálogo (ex.: lançamento ainda não cadastrado): nunca some.
            "materiais": [
                _publico(m) for m in materiais
                if codigo_linha in m["linhas"] and (not (m["equipamentos"] or m["termos"]) or m["url"] not in vinculados)
            ],
        })
    gerais = [_publico(m) for m in materiais if not m["linhas"] and not m["equipamentos"] and not m["termos"]]
    linktree = str(materiais_conteudo.get("linktree_url") or "").strip()
    return {
        "fonte": fonte,
        "precos_visiveis": ver_precos,
        "linktree_url": linktree if linktree.startswith("https://") else None,
        "materiais_gerais": gerais,
        "linhas": linhas_saida,
        "total_equipamentos": sum(len(l["equipamentos"]) for l in linhas_saida),
    }


def carregar_vitrine(*, ver_precos: bool, hoje: date) -> dict[str, Any]:
    try:
        equipamentos, precos = _ler_catalogo_comercial()
        fonte = "catalogo_comercial"
        if not equipamentos:
            raise LookupError("catálogo comercial vazio")
    except Exception:
        equipamentos, precos, fonte = _equipamentos_do_catalogo_oficial(), [], "catalogo_oficial_sem_precos"
    vitrine = montar_vitrine(equipamentos=equipamentos, precos=precos, materiais_conteudo=_materiais_brutos(),
                             ver_precos=ver_precos and fonte == "catalogo_comercial", hoje=hoje, fonte=fonte)
    vitrine["tabela_aplicacao"] = tabela_aplicacao()
    vitrine["materiais_internos"] = materiais_internos()
    return vitrine
