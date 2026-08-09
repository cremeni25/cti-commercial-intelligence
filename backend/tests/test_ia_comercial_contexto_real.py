from services.ia_comercial_cti import _oportunidade_aberta, _pedido_em_curso


def test_ganho_nao_e_oportunidade_aberta():
    assert _oportunidade_aberta({"status": "GANHO"}) is False
    assert _oportunidade_aberta({"status": "PERDIDO"}) is False
    assert _oportunidade_aberta({"status": "NEGOCIACAO"}) is True


def test_pedido_permanece_em_curso_ate_encerramento():
    assert _pedido_em_curso({"status": "ABERTO"}) is True
    assert _pedido_em_curso({"status": "FATURADO"}) is True
    assert _pedido_em_curso({"status": "ENTREGUE"}) is True
    assert _pedido_em_curso({"status": "INSTALADO"}) is True
    assert _pedido_em_curso({"status": "ENCERRADO"}) is False
    assert _pedido_em_curso({"status": "CANCELADO"}) is False
