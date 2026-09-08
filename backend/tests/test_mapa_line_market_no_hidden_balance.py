from services.mapa_line_market import composicao_marca_linha


def test_status_sem_marca_permanece_visivel_no_saldo():
    resultado = composicao_marca_linha([
        {"quantidade": 18, "status": "", "fabricante_equipamento": ""},
    ])
    assert resultado["mercado"] == 18
    assert resultado["marca_nao_discriminada"] == 18
    assert resultado["fechamento_total"] == 18
    assert resultado["fechamento_ok"] is True
