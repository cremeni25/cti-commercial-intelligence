from routers.propostas_primeira_pagina_router import _venda_indireta


def test_identifica_venda_indireta_pelo_titulo():
    proposta = {"snapshot_dados": {"oportunidade": {"titulo": "Venda Indireta"}}}
    assert _venda_indireta(proposta) is True


def test_venda_direta_nao_e_reclassificada():
    proposta = {"snapshot_dados": {"oportunidade": {"titulo": "Venda Direta"}}}
    assert _venda_indireta(proposta) is False
