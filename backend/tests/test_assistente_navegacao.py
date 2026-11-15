"""Pergunte ao CTI: pergunta → resposta curta + tela filtrada (dados fictícios)."""
from urllib.parse import parse_qs, urlparse

from services import assistente_navegacao as assistente
from tests.test_carteira_setorizada import base  # noqa: F401  (fixture)


def _consulta(href):
    return {k: v[0] for k, v in parse_qs(urlparse(href).query).items()}


def test_filtro_por_sinal_porte_e_link_da_carteira(base):  # noqa: F811
    r = assistente.perguntar("Quais clientes com frota grande usam Thermo King?", None, True)
    assert r["resposta"].startswith("1 ") and "Transportes Gama" in r["resposta"]
    carteira = r["acoes"][0]
    assert carteira["href"].startswith("/carteira?") and _consulta(carteira["href"]) == {"sinal": "USA_CONCORRENTE", "porte": "GRANDE"}
    assert r["acoes"][-1]["href"].startswith("/ia-comercial?prompt=")


def test_inativos_e_escopo_do_vendedor(base):  # noqa: F811
    empresa = assistente.perguntar("clientes inativos", None, True)
    assert empresa["resposta"].startswith("1 clientes inativos na empresa")
    ana = assistente.perguntar("clientes inativos", "ana", True)  # o inativo é do Beto
    assert ana["resposta"] == "Nenhum resultado para clientes inativos na sua carteira."


def test_empresa_citada_abre_a_ficha(base):  # noqa: F811
    r = assistente.perguntar("como está a Frios Alfa?", None, True)
    assert r["resposta"].startswith("Frios Alfa Ltda: clientes ativos")
    assert _consulta(r["acoes"][0]["href"]) == {"empresa": "ativo"}


def test_sem_carteira_so_telas_e_ia(base):  # noqa: F811
    r = assistente.perguntar("onde vejo as propostas?", "x", False)
    assert r["acoes"][0]["href"] == "/propostas"
    assert "Frios" not in str(r)
    vazio = assistente.perguntar("bom dia", None, True)
    assert [a["href"].split("?")[0] for a in vazio["acoes"]] == ["/ia-comercial"]


def test_busca_universal(base):  # noqa: F811
    r = assistente.buscar("gama", None, True)
    assert r["empresas"][0]["nome"] == "Transportes Gama"
    assert assistente.buscar("gama", "ana", True)["empresas"] == []  # fora da carteira da Ana
    assert assistente.buscar("33333", None, True)["empresas"][0]["cliente_id"] == "prospect-frota"
    assert any(e["modelo"].startswith("CITIMAX") for e in assistente.buscar("citimax", None, False)["equipamentos"])
    assert assistente.buscar("propost", None, False)["telas"][0]["href"] == "/propostas"


def test_redacao_da_resposta(base):  # noqa: F811
    r = assistente.perguntar("prospects com frota grande que usam concorrente", None, True)
    assert r["resposta"].startswith("1 prospects com frota (frota grande) que usam concorrente na empresa.")
