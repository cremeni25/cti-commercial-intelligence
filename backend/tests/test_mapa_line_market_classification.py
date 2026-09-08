from routers import crm_scope_mapa_insights_router as insights
from services.mapa_line_market import composicao_marca_linha


def test_fabricante_zero_permanece_nao_discriminado():
    resultado = composicao_marca_linha([
        {"id": "r1", "quantidade": 3, "status": "", "fabricante_equipamento": 0},
    ], classificacoes_cti={})
    assert resultado["mercado"] == 3
    assert resultado["marca_nao_discriminada"] == 3
    assert resultado["outras_marcas"] == 0
    assert resultado["fechamento_ok"] is True


def test_classificacao_cti_enriquece_marca_sem_alterar_denominador():
    resultado = composicao_marca_linha([
        {"id": "r1", "quantidade": 4, "status": "Nacional", "fabricante_equipamento": ""},
    ], classificacoes_cti={"r1": "ZANOTTI"})
    assert resultado["mercado"] == 4
    assert resultado["outras_marcas"] == 4
    assert resultado["marcas_concorrentes"] == [
        {"nome": "ZANOTTI", "quantidade": 4, "percentual_mercado": 100.0}
    ]
    assert resultado["fechamento_ok"] is True


def test_sem_mes_nao_inventa_pico_janeiro():
    leitura, _ = insights._leitura_linha("Trailer", [0] * 12, 5)
    assert "não há competência mensal suficiente" in leitura
    assert "Jan" not in leitura
