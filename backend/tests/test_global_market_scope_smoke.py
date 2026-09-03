from services.anfir_market_scope import filtrar_mercado_real_viena, implementadora_fora_escopo


def test_regra_global_remove_exclusoes_sem_apagar_fonte():
    bruto = [
        {"implementadora": "Fibra West"},
        {"implementadora": "HIGH FLEX"},
        {"implementadora": "Planalto"},
        {"implementadora": "Ibiporã"},
    ]
    real = filtrar_mercado_real_viena(bruto)

    assert len(bruto) == 4
    assert len(real) == 1
    assert real[0]["implementadora"] == "Ibiporã"
    assert all(implementadora_fora_escopo(item) is None for item in real)
