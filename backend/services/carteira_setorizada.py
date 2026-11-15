"""Carteira setorizada e ficha única por empresa.

Cada cliente do CRM é cruzado, pelo CNPJ e, na falta dele, pelo nome
padronizado, com:
- ANFIR (frota registrada, fabricante dos equipamentos, implementadora);
- negócios do CRM (em aberto e ganhos) e pedidos;
- planilhas comerciais (vendas realizadas e NEGOCIAÇÕES).

Daí saem os grupos de setorização, que servem para a gestão priorizar
abordagens e, na próxima etapa, para o agente e o atendimento automático.
"""
from __future__ import annotations

import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from threading import Lock
from typing import Any

from core.cti_taxonomy import consolidar_cliente
from services.acervo_comercial import atividade_feita, negocio_encerrado, paginar

MESES_CLIENTE_ATIVO = 24
ANOS_JANELA_RENOVACAO = 6
STATUS_CARRIER = {"CARRIER", "USADOCARRIER"}
STATUS_CONCORRENCIA = {"TK", "NACIONAL", "USADOCONCORRENTE"}

GRUPOS = {
    "CLIENTE_ATIVO": "Cliente ativo (comprou nos últimos 24 meses)",
    "CLIENTE_INATIVO": "Cliente inativo (última compra há mais de 24 meses)",
    "PROSPECT_COM_FROTA": "Prospect com frota registrada (nunca comprou)",
    "PROSPECT": "Prospect sem frota conhecida",
}
PORTES = {"GRANDE": "Frota grande (20+)", "MEDIO": "Frota média (5 a 19)", "PEQUENO": "Frota pequena (1 a 4)", "SEM_DADO": "Frota não identificada"}
SINAIS = {
    "RECORRENTE": "Comprou em mais de um ano",
    "JANELA_RENOVACAO": "Equipamentos com 6+ anos: janela de renovação",
    "USA_CONCORRENTE": "Tem equipamentos da concorrência",
    "NEGOCIO_ABERTO": "Tem negócio em andamento",
    "SEM_RESPONSAVEL": "Sem responsável comercial",
}

_cache: dict[str, Any] = {}
_trava = Lock()
VALIDADE_CACHE_S = 600


def _supabase():
    from core.supabase_client import supabase

    return supabase


def _cnpj(valor: Any) -> str:
    digitos = re.sub(r"\D", "", str(valor or ""))
    return digitos if len(digitos) == 14 else ""


def _nome(valor: Any) -> str:
    try:
        return str(consolidar_cliente(valor) or "").strip().upper()
    except Exception:
        texto = str(valor or "").strip().upper()
        return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _data(valor: Any) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor or "").strip()[:10]
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def _data_anfir(registro: dict[str, Any]) -> date | None:
    try:
        from services.operational_filters import data_registro

        return data_registro(registro)
    except Exception:
        return _data(registro.get("data") or registro.get("created_at"))


def _status_anfir(registro: dict[str, Any]) -> str:
    texto = str(registro.get("status") or "").strip().upper()
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).replace(" ", "")


def _numero(valor: Any, padrao: float = 0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


class _Indice:
    """Agrupa registros de uma fonte por CNPJ e por nome padronizado."""

    def __init__(self) -> None:
        self.por_cnpj: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.por_nome: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add(self, registro: dict[str, Any], cnpj: Any, nome: Any) -> None:
        chave_cnpj = _cnpj(cnpj)
        if chave_cnpj:
            self.por_cnpj[chave_cnpj].append(registro)
        elif _nome(nome):
            self.por_nome[_nome(nome)].append(registro)

    def do_cliente(self, cliente: dict[str, Any]) -> list[dict[str, Any]]:
        vistos: set[int] = set()
        saida = []
        for registro in self.por_cnpj.get(_cnpj(cliente.get("cnpj")), []) + self.por_nome.get(_nome(cliente.get("nome")), []):
            if id(registro) not in vistos:
                vistos.add(id(registro))
                saida.append(registro)
        return saida


def _carregar_fontes() -> dict[str, Any]:
    from repositories.cti_repository import CTIRepository
    from services import planilhas_comerciais

    clientes = paginar("clientes", "*")
    try:
        anfir = CTIRepository().buscar_cti_anfir()
    except Exception:
        anfir = []
    oportunidades = paginar("cti_oportunidades", "*", lambda q: q.is_("arquivado_em", "null"))
    try:
        pedidos = paginar("cti_pedidos", "*")
    except Exception:
        pedidos = []
    atividades = paginar("cti_atividades", "id,cliente_id,usuario_id,status,data,tipo,titulo")
    usuarios = {str(u["id"]): u for u in (_supabase().table("cti_users").select("id,nome,ativo,status_acesso").execute().data or []) if u.get("id")}
    try:
        vendas_planilha = planilhas_comerciais.registros("vendas_realizadas")
        negociacoes = planilhas_comerciais.registros("negociacoes_andamento")
    except Exception:
        vendas_planilha, negociacoes = [], []
    return {"clientes": clientes, "anfir": anfir, "oportunidades": oportunidades, "pedidos": pedidos, "atividades": atividades,
            "usuarios": usuarios, "vendas_planilha": vendas_planilha, "negociacoes": negociacoes}


def _perfil(cliente: dict[str, Any], fontes: dict[str, Any], indices: dict[str, Any], hoje: date) -> dict[str, Any]:
    cid = str(cliente.get("id"))
    anfir = indices["anfir"].do_cliente(cliente)
    frota_total = sum(max(_numero(r.get("quantidade"), 1), 1) for r in anfir)
    frota_carrier = sum(max(_numero(r.get("quantidade"), 1), 1) for r in anfir if _status_anfir(r) in STATUS_CARRIER)
    frota_concorrencia = sum(max(_numero(r.get("quantidade"), 1), 1) for r in anfir if _status_anfir(r) in STATUS_CONCORRENCIA)
    datas_anfir = [d for d in (_data_anfir(r) for r in anfir) if d]

    oportunidades = indices["oportunidades"].get(cid, [])
    abertos = [o for o in oportunidades if not negocio_encerrado(o)]
    ganhos = [o for o in oportunidades if str(o.get("status") or "").upper() in {"GANHO", "FATURADO"}]
    pedidos = indices["pedidos"].get(cid, [])
    vendas = indices["vendas"].do_cliente(cliente)

    datas_compra = sorted(d for d in (
        [_data(v.get("data_emissao") or v.get("mes")) for v in vendas]
        + [_data(p.get("created_at")) for p in pedidos]
        + [_data(o.get("data_fechamento_real") or o.get("updated_at")) for o in ganhos]
    ) if d)
    ultima_compra = datas_compra[-1] if datas_compra else None
    unidades_compradas = int(sum(_numero(v.get("quantidade"), 1) for v in vendas))

    if ultima_compra:
        meses = (hoje.year - ultima_compra.year) * 12 + hoje.month - ultima_compra.month
        grupo = "CLIENTE_ATIVO" if meses <= MESES_CLIENTE_ATIVO else "CLIENTE_INATIVO"
    else:
        grupo = "PROSPECT_COM_FROTA" if frota_total else "PROSPECT"
    porte = "GRANDE" if frota_total >= 20 else "MEDIO" if frota_total >= 5 else "PEQUENO" if frota_total >= 1 else "SEM_DADO"

    sinais = []
    if len({d.year for d in datas_compra}) >= 2:
        sinais.append("RECORRENTE")
    # Equipamento mais novo conhecido (última compra ou último registro de frota): se tem 6+ anos, é hora de renovar.
    referencia_frota = max([d for d in [ultima_compra, *datas_anfir] if d], default=None)
    if referencia_frota and (hoje - referencia_frota).days >= ANOS_JANELA_RENOVACAO * 365:
        sinais.append("JANELA_RENOVACAO")
    if frota_concorrencia:
        sinais.append("USA_CONCORRENTE")
    if abertos:
        sinais.append("NEGOCIO_ABERTO")
    responsavel_id = str(cliente.get("responsavel_comercial_id") or "")
    if not responsavel_id:
        sinais.append("SEM_RESPONSAVEL")
    responsavel = fontes["usuarios"].get(responsavel_id, {})

    implementadoras = Counter(str(r.get("implementadora") or "").strip() for r in anfir if r.get("implementadora"))
    return {
        "cliente_id": cid, "nome": cliente.get("nome"), "cnpj": cliente.get("cnpj"), "cidade": cliente.get("cidade"),
        "estado": cliente.get("estado"), "sub_regiao": cliente.get("sub_regiao"),
        "segmento": cliente.get("segmento") or cliente.get("categoria"),
        "responsavel_id": responsavel_id or None, "responsavel_nome": responsavel.get("nome"),
        "responsavel_ativo": bool(responsavel) and responsavel.get("ativo") is not False,
        "grupo": grupo, "porte": porte, "sinais": sinais,
        "frota_registrada": int(frota_total), "frota_carrier": int(frota_carrier), "frota_concorrencia": int(frota_concorrencia),
        "implementadora_principal": implementadoras.most_common(1)[0][0] if implementadoras else None,
        "ultimo_registro_anfir": max(datas_anfir).isoformat() if datas_anfir else None,
        "ultima_compra": ultima_compra.isoformat() if ultima_compra else None,
        "compras": len(datas_compra), "unidades_compradas": unidades_compradas,
        "negocios_abertos": len(abertos), "valor_negocios_abertos": round(sum(_numero(o.get("valor_total") or o.get("valor")) for o in abertos), 2),
    }


def _indices(fontes: dict[str, Any]) -> dict[str, Any]:
    anfir, vendas = _Indice(), _Indice()
    for registro in fontes["anfir"]:
        anfir.add(registro, registro.get("cnpj"), registro.get("cliente") or registro.get("razao_social"))
    # NEGOCIAÇÕES liga nome a CNPJ; com isso as vendas (só com nome) também casam pelo CNPJ.
    cnpj_por_nome = {_nome(n.get("cliente")): _cnpj(n.get("cnpj")) for n in fontes["negociacoes"] if _cnpj(n.get("cnpj"))}
    for venda in fontes["vendas_planilha"]:
        vendas.add(venda, cnpj_por_nome.get(_nome(venda.get("cliente")), ""), venda.get("cliente"))
    por_cliente: dict[str, dict[str, list[dict[str, Any]]]] = {"oportunidades": defaultdict(list), "pedidos": defaultdict(list), "atividades": defaultdict(list)}
    for chave, lista in (("oportunidades", fontes["oportunidades"]), ("pedidos", fontes["pedidos"]), ("atividades", fontes["atividades"])):
        for registro in lista:
            if registro.get("cliente_id"):
                por_cliente[chave][str(registro["cliente_id"])].append(registro)
    return {"anfir": anfir, "vendas": vendas, **por_cliente}


def _carteira_completa() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    with _trava:
        if "perfis" in _cache and time.monotonic() - _cache["em"] < VALIDADE_CACHE_S:
            return _cache["perfis"], _cache["fontes"], _cache["indices"]
    fontes = _carregar_fontes()
    indices = _indices(fontes)
    hoje = datetime.now(timezone.utc).date()
    perfis = [_perfil(c, fontes, indices, hoje) for c in fontes["clientes"] if c.get("id") and not c.get("arquivado_em")]
    with _trava:
        _cache.update({"perfis": perfis, "fontes": fontes, "indices": indices, "em": time.monotonic()})
    return perfis, fontes, indices


def limpar_cache() -> None:
    with _trava:
        _cache.clear()


def _prioridade(p: dict[str, Any]) -> tuple:
    ordem_grupo = {"CLIENTE_INATIVO": 0, "PROSPECT_COM_FROTA": 1, "CLIENTE_ATIVO": 2, "PROSPECT": 3}
    return (0 if "JANELA_RENOVACAO" in p["sinais"] else 1, ordem_grupo.get(p["grupo"], 9), -p["frota_registrada"], str(p["nome"] or ""))


def setorizacao(responsavel_id: str | None = None, grupo: str | None = None, sinal: str | None = None, limite: int = 300,
                porte: str | None = None, cidade: str | None = None) -> dict[str, Any]:
    perfis, _, _ = _carteira_completa()
    base = [p for p in perfis if not responsavel_id or p["responsavel_id"] == responsavel_id]
    cidade_alvo = _nome(cidade) if cidade else ""
    filtrados = [p for p in base if (not grupo or p["grupo"] == grupo) and (not sinal or sinal in p["sinais"])
                 and (not porte or p["porte"] == porte) and (not cidade_alvo or _nome(p.get("cidade")) == cidade_alvo)]
    filtrados.sort(key=_prioridade)
    return {
        "total_clientes": len(base),
        "por_grupo": {g: sum(1 for p in base if p["grupo"] == g) for g in GRUPOS},
        "por_porte": {g: sum(1 for p in base if p["porte"] == g) for g in PORTES},
        "por_sinal": {s: sum(1 for p in base if s in p["sinais"]) for s in SINAIS},
        "rotulos": {"grupos": GRUPOS, "portes": PORTES, "sinais": SINAIS},
        "filtrados": len(filtrados),
        "clientes": filtrados[:limite],
    }


def ficha(cliente_id: str) -> dict[str, Any] | None:
    perfis, fontes, indices = _carteira_completa()
    perfil = next((p for p in perfis if p["cliente_id"] == str(cliente_id)), None)
    if not perfil:
        return None
    cliente = next(c for c in fontes["clientes"] if str(c.get("id")) == str(cliente_id))
    usuarios = fontes["usuarios"]
    nome_usuario = lambda uid: (usuarios.get(str(uid or "")) or {}).get("nome")  # noqa: E731
    try:
        historico = _supabase().table("cti_cliente_responsabilidade_historico").select("*").eq("cliente_id", str(cliente_id)).execute().data or []
    except Exception:
        historico = []
    anfir = indices["anfir"].do_cliente(cliente)
    atividades = sorted(indices["atividades"].get(str(cliente_id), []), key=lambda a: str(a.get("data") or ""), reverse=True)
    return {
        **perfil,
        "cadastro": {k: cliente.get(k) for k in ("nome", "cnpj", "cidade", "estado", "endereco", "bairro", "cep", "contato", "fone", "email", "segmento", "categoria", "sub_regiao", "ddd")},
        "responsaveis_anteriores": [{"de": nome_usuario(h.get("responsavel_anterior_id")), "para": nome_usuario(h.get("responsavel_novo_id")), "quando": h.get("created_at"), "motivo": h.get("motivo")} for h in sorted(historico, key=lambda h: str(h.get("created_at") or ""), reverse=True)],
        "negocios": [{"id": o.get("id"), "titulo": o.get("titulo"), "status": o.get("status"), "valor": o.get("valor_total") or o.get("valor"), "responsavel": nome_usuario(o.get("responsavel_id")), "encerrado": negocio_encerrado(o)} for o in indices["oportunidades"].get(str(cliente_id), [])],
        "atividades_recentes": [{"data": a.get("data"), "tipo": a.get("tipo"), "titulo": a.get("titulo"), "status": a.get("status"), "autor": nome_usuario(a.get("usuario_id")), "feita": atividade_feita(a)} for a in atividades[:15]],
        "compras_planilha": [{"mes": v.get("mes"), "equipamento": v.get("equipamento"), "quantidade": v.get("quantidade"), "vendedor": v.get("vendedor")} for v in indices["vendas"].do_cliente(cliente)][:50],
        "frota_por_implementadora": dict(Counter(str(r.get("implementadora") or "Não informada") for r in anfir).most_common(10)),
        "frota_por_fabricante": {"Carrier": perfil["frota_carrier"], "Concorrência": perfil["frota_concorrencia"], "Outros/sem informação": max(perfil["frota_registrada"] - perfil["frota_carrier"] - perfil["frota_concorrencia"], 0)},
    }
