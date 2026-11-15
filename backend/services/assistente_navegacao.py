"""Pergunte ao CTI: transforma uma pergunta em resposta curta + tela certa com filtro.

Não elimina telas nem caminhos: lê a pergunta, responde com os números da carteira
e devolve o atalho para a tela completa já filtrada. O que não reconhece segue
para a IA Comercial com a pergunta preenchida.

A interpretação é determinística (palavras do vocabulário comercial do CTI), sem
custo de modelo e com resposta imediata.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any
from urllib.parse import urlencode

from services import carteira_setorizada as carteira


def dobrar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").lower())
    return re.sub(r"\s+", " ", "".join(c for c in base if not unicodedata.combining(c))).strip()


GRUPOS = [
    (("prospects com frota", "prospect com frota", "com frota e sem compra", "nunca compraram"), "PROSPECT_COM_FROTA"),
    (("inativo", "inativos", "parado", "parados", "nao compra", "sem comprar", "reativ"), "CLIENTE_INATIVO"),
    (("clientes ativos", "cliente ativo", "compraram recentemente"), "CLIENTE_ATIVO"),
    (("prospect", "prospects", "prospeccao"), "PROSPECT"),
]
SINAIS = [
    (("renovacao", "renovar", "frota velha", "frota antiga", "equipamento velho", "6 anos", "seis anos"), "JANELA_RENOVACAO"),
    (("concorr", "thermo king", "thermoking", " tk ", "outro fabricante", "outra marca"), "USA_CONCORRENTE"),
    (("negocio aberto", "negocios abertos", "negociacao em andamento", "em negociacao"), "NEGOCIO_ABERTO"),
    (("sem responsavel", "sem vendedor", "sem dono", "orfa", "orfao"), "SEM_RESPONSAVEL"),
    (("recorrente", "recorrentes", "compra sempre", "fieis"), "RECORRENTE"),
]
PORTES = [
    (("frota grande", "frotas grandes", "grande frota", "grandes frotas", "grandes"), "GRANDE"),
    (("frota media", "frotas medias", "medias", "medio porte"), "MEDIO"),
    (("frota pequena", "frotas pequenas", "pequenos", "pequeno porte"), "PEQUENO"),
]

# Telas: palavras que levam a cada uma (a permissão é conferida no navegador).
TELAS: list[dict[str, Any]] = [
    {"href": "/central", "titulo": "Central de Inteligência", "palavras": ("central", "prioridade", "prioridades", "o que fazer", "hoje", "riscos")},
    {"href": "/carteira", "titulo": "Carteira setorizada", "palavras": ("carteira", "meus clientes", "clientes", "segmento", "setoriz")},
    {"href": "/atividades/interacao", "titulo": "Nova interação", "palavras": ("registrar", "registra", "nova interacao", "nova visita", "anotar", "lancar visita")},
    {"href": "/atividades", "titulo": "Atividades e agenda", "palavras": ("agenda", "atividade", "atividades", "visita", "visitas", "ligacao", "tarefa")},
    {"href": "/oportunidades", "titulo": "Oportunidades", "palavras": ("oportunidade", "oportunidades", "negocio", "negocios")},
    {"href": "/pipeline", "titulo": "Pipeline", "palavras": ("pipeline", "funil", "etapa", "etapas")},
    {"href": "/propostas", "titulo": "Propostas", "palavras": ("proposta", "propostas", "orcamento", "cotacao")},
    {"href": "/pedidos", "titulo": "Pedidos", "palavras": ("pedido", "pedidos", "entrega", "faturamento")},
    {"href": "/vendas", "titulo": "Vendas", "palavras": ("venda", "vendas", "vendido", "vendemos", "resultado")},
    {"href": "/forecast", "titulo": "Forecast", "palavras": ("forecast", "previsao", "projecao", "meta")},
    {"href": "/relatorios", "titulo": "Relatórios", "palavras": ("relatorio", "relatorios", "imprimir", "exportar")},
    {"href": "/catalogo", "titulo": "Catálogo de Produtos", "palavras": ("catalogo", "produto", "produtos", "modelo", "modelos", "preco", "tabela de aplicacao", "bau", "temperatura", "citimax", "supra", "vector")},
    {"href": "/mapa-estrategico", "titulo": "Mapa Estratégico", "palavras": ("mapa", "territorio", "regiao", "regioes", "cidade", "cidades")},
    {"href": "/inteligencia", "titulo": "Inteligência de Mercado", "palavras": ("mercado", "anfir", "market share", "participacao", "emplacamento")},
    {"href": "/implementadoras", "titulo": "Implementadoras", "palavras": ("implementadora", "implementadoras", "encarrocador", "facchini", "randon", "librelato")},
    {"href": "/crm-app/feiras", "titulo": "Feiras e Eventos", "palavras": ("feira", "feiras", "evento", "eventos", "fenatran")},
    {"href": "/campanhas", "titulo": "Campanhas e Canal", "palavras": ("campanha", "campanhas", "whatsapp", "canal", "lgpd", "disparo")},
    {"href": "/acervo", "titulo": "Acervo comercial", "palavras": ("acervo", "backup", "copia de seguranca", "transferir carteira", "quem saiu")},
    {"href": "/empresas", "titulo": "Empresas", "palavras": ("empresa", "empresas", "cadastro", "cnpj")},
    {"href": "/usuarios", "titulo": "Usuários", "palavras": ("usuario", "usuarios", "senha", "acesso", "permissao")},
]

ROTULO_GRUPO = {"CLIENTE_ATIVO": "clientes ativos", "CLIENTE_INATIVO": "clientes inativos", "PROSPECT_COM_FROTA": "prospects com frota", "PROSPECT": "prospects"}
ROTULO_SINAL = {"JANELA_RENOVACAO": "na janela de renovação", "USA_CONCORRENTE": "que usam concorrente", "NEGOCIO_ABERTO": "com negócio aberto",
                "SEM_RESPONSAVEL": "sem responsável", "RECORRENTE": "recorrentes"}
ROTULO_PORTE = {"GRANDE": "(frota grande)", "MEDIO": "(frota média)", "PEQUENO": "(frota pequena)"}


def _primeiro(texto: str, tabela: list[tuple[tuple[str, ...], str]]) -> str | None:
    alvo = f" {texto} "
    for palavras, codigo in tabela:
        if any(p in alvo for p in palavras):
            return codigo
    return None


def _contem_palavra(texto: str, termo: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(termo)}(?![a-z0-9])", texto))


def _escopo(perfis: list[dict[str, Any]], responsavel_id: str | None) -> list[dict[str, Any]]:
    return [p for p in perfis if responsavel_id is None or p["responsavel_id"] == responsavel_id]


def _cidade(texto: str, perfis: list[dict[str, Any]]) -> str | None:
    cidades = {dobrar(p.get("cidade")): p.get("cidade") for p in perfis if p.get("cidade") and len(dobrar(p.get("cidade"))) >= 4}
    achadas = [c for c in cidades if _contem_palavra(texto, c)]
    return cidades[max(achadas, key=len)] if achadas else None


def _empresa(texto: str, perfis: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Empresa citada pelo nome (o maior nome contido na pergunta, com 5+ letras)."""
    melhor = None
    for p in perfis:
        nome = dobrar(p.get("nome"))
        nucleo = re.sub(r"\b(ltda|me|eireli|s a|sa|epp|transportes?|comercio|industria|logistica)\b", " ", nome)
        nucleo = re.sub(r"\s+", " ", nucleo).strip()
        for candidato in {nome, nucleo}:
            if len(candidato) >= 5 and _contem_palavra(texto, candidato) and (not melhor or len(candidato) > melhor[0]):
                melhor = (len(candidato), p)
    return melhor[1] if melhor else None


def _telas(texto: str) -> list[dict[str, str]]:
    alvo = f" {texto} "
    pontos = []
    for tela in TELAS:
        acertos = sum(1 for p in tela["palavras"] if p in alvo)
        if acertos:
            pontos.append((acertos, tela))
    pontos.sort(key=lambda par: -par[0])
    return [{"href": t["href"], "titulo": t["titulo"]} for _, t in pontos[:3]]


def _link_carteira(filtros: dict[str, str]) -> str:
    consulta = {k: v for k, v in filtros.items() if v}
    return "/carteira" + (f"?{urlencode(consulta)}" if consulta else "")


def perguntar(pergunta: str, responsavel_id: str | None, pode_ver_carteira: bool) -> dict[str, Any]:
    """Resposta curta + ações. ``responsavel_id`` None = visão da empresa inteira (gestão)."""
    texto = dobrar(pergunta)
    acoes: list[dict[str, str]] = []
    resposta = ""
    destaques: list[dict[str, Any]] = []

    if pode_ver_carteira:
        perfis, _, _ = carteira._carteira_completa()
        base = _escopo(perfis, responsavel_id)
        empresa = _empresa(texto, base)
        grupo, sinal, porte = _primeiro(texto, GRUPOS), _primeiro(texto, SINAIS), _primeiro(texto, PORTES)
        cidade = _cidade(texto, base)
        if empresa:
            p = empresa
            partes = [f"{p['nome']}: {ROTULO_GRUPO.get(p['grupo'], p['grupo'])}",
                      f"frota registrada {p['frota_registrada']} ({p['frota_concorrencia']} da concorrência)",
                      f"última compra {p['ultima_compra'] or 'sem registro'}",
                      f"responsável {p['responsavel_nome'] or 'nenhum'}"]
            if p["negocios_abertos"]:
                partes.append(f"{p['negocios_abertos']} negócio(s) aberto(s)")
            resposta = "; ".join(partes) + "."
            acoes.append({"href": _link_carteira({"empresa": p["cliente_id"]}), "titulo": "Abrir a ficha completa da empresa"})
        elif grupo or sinal or porte or cidade:
            filtrados = [p for p in base if (not grupo or p["grupo"] == grupo) and (not sinal or sinal in p["sinais"])
                         and (not porte or p["porte"] == porte) and (not cidade or dobrar(p.get("cidade")) == dobrar(cidade))]
            filtrados.sort(key=carteira._prioridade)
            descricao = " ".join(filter(None, [ROTULO_GRUPO.get(grupo or "", "clientes e prospects"), ROTULO_PORTE.get(porte or ""),
                                                ROTULO_SINAL.get(sinal or ""), f"em {cidade}" if cidade else None]))
            escopo = "na sua carteira" if responsavel_id else "na empresa"
            if filtrados:
                nomes = ", ".join(str(p["nome"]) for p in filtrados[:3])
                resposta = f"{len(filtrados)} {descricao} {escopo}. Os primeiros pela prioridade: {nomes}."
            else:
                resposta = f"Nenhum resultado para {descricao} {escopo}."
            destaques = [{"cliente_id": p["cliente_id"], "nome": p["nome"], "cidade": p.get("cidade"), "frota": p["frota_registrada"]} for p in filtrados[:5]]
            acoes.append({"href": _link_carteira({"grupo": grupo or "", "sinal": sinal or "", "porte": porte or "", "cidade": cidade or ""}),
                          "titulo": f"Abrir na Carteira com esse filtro ({len(filtrados)})"})

    for tela in _telas(texto):
        if not any(a["href"].split("?")[0] == tela["href"] for a in acoes):
            acoes.append({"href": tela["href"], "titulo": f"Abrir {tela['titulo']}"})

    if not resposta:
        resposta = "Encontrei estas telas para o que você pediu." if acoes else "Não reconheci o pedido. A IA Comercial pode analisar com mais profundidade."
    acoes.append({"href": "/ia-comercial?" + urlencode({"prompt": pergunta.strip()}), "titulo": "Perguntar à IA Comercial"})
    return {"pergunta": pergunta, "resposta": resposta, "destaques": destaques, "acoes": acoes}


_CACHE_MODELOS: dict[str, Any] = {}


def _modelos_catalogo() -> list[dict[str, Any]]:
    """Modelos do catálogo (mesma fonte da vitrine: comercial, ou o oficial como reserva) + Tabela de Aplicação."""
    import time

    from services import catalogo_vitrine

    if _CACHE_MODELOS and time.monotonic() - _CACHE_MODELOS["em"] < 600:
        return _CACHE_MODELOS["modelos"]
    try:
        equipamentos, _ = catalogo_vitrine._ler_catalogo_comercial()
        if not equipamentos:
            raise LookupError("catálogo comercial vazio")
    except Exception:
        try:
            equipamentos = catalogo_vitrine._equipamentos_do_catalogo_oficial()
        except Exception:
            equipamentos = []
    vistos: dict[str, dict[str, Any]] = {}
    for e in equipamentos:
        nome = str(e.get("nome_comercial") or e.get("modelo_base") or "").strip()
        if nome:
            vistos.setdefault(dobrar(nome), {"modelo": nome, "linha": e.get("linha_produto")})
    for e in (catalogo_vitrine.tabela_aplicacao() or {}).get("equipamentos") or []:
        if e.get("modelo"):
            vistos.setdefault(dobrar(e["modelo"]), {"modelo": e["modelo"], "linha": e.get("linha")})
    modelos = list(vistos.values())
    _CACHE_MODELOS.update({"modelos": modelos, "em": time.monotonic()})
    return modelos


def buscar(termo: str, responsavel_id: str | None, pode_ver_carteira: bool, limite: int = 8) -> dict[str, Any]:
    """Busca universal: telas, empresas da carteira e modelos de equipamento."""
    alvo = dobrar(termo)
    digitos = re.sub(r"\D", "", termo)
    resultado: dict[str, Any] = {"telas": [], "empresas": [], "equipamentos": []}
    if len(alvo) < 2:
        return resultado
    resultado["telas"] = [{"href": t["href"], "titulo": t["titulo"]} for t in TELAS
                          if alvo in dobrar(t["titulo"]) or any(alvo in p or p in alvo for p in t["palavras"] if len(p) >= 4)][:5]
    if pode_ver_carteira:
        perfis, _, _ = carteira._carteira_completa()
        achados = []
        for p in _escopo(perfis, responsavel_id):
            cnpj = re.sub(r"\D", "", str(p.get("cnpj") or ""))
            if alvo in dobrar(p.get("nome")) or (len(digitos) >= 4 and digitos in cnpj):
                achados.append(p)
        achados.sort(key=lambda p: (not dobrar(p.get("nome")).startswith(alvo), carteira._prioridade(p)))
        resultado["empresas"] = [{"cliente_id": p["cliente_id"], "nome": p["nome"], "cidade": p.get("cidade"), "grupo": p["grupo"],
                                  "href": _link_carteira({"empresa": p["cliente_id"]})} for p in achados[:limite]]
    resultado["equipamentos"] = [{"modelo": m["modelo"], "linha": m["linha"], "href": "/catalogo?" + urlencode({"busca": m["modelo"]})}
                                 for m in _modelos_catalogo() if alvo in dobrar(m["modelo"])][:5]
    return resultado
