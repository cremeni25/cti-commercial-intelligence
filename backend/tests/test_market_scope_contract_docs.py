from services.anfir_market_scope import IMPLEMENTADORAS_FORA_ESCOPO


def test_contrato_nominal_do_mercado_real_viena():
    assert IMPLEMENTADORAS_FORA_ESCOPO == ("FIBRA WEST", "HIGH FLEX", "PLANALTO")
