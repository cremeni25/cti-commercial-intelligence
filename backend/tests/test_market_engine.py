from engine.market_engine import MarketEngine


def test_market_engine_usa_implementadora_como_chave_oficial():
    engine = MarketEngine([
        {"estado": "SP", "segmento": "TRAILER", "linha": "VECTOR 8500", "implementadora": "RANDON"},
        {"estado": "SP", "segmento": "TRAILER", "linha": "VECTOR 8500", "implementador": "FACCHINI"},
    ])

    share = engine.oem_share()
    assert {item["implementadora"] for item in share} == {"RANDON", "FACCHINI"}
    assert all("implementador" not in item for item in share)

    dominance = engine.market_dominance()
    assert {item["implementadora"] for item in dominance} == {"RANDON", "FACCHINI"}
    assert all("implementador" not in item for item in dominance)


def test_market_engine_mantem_registros_sem_implementadora_nos_totais_gerais():
    engine = MarketEngine([
        {"estado": "SP", "segmento": "TRAILER", "linha": "VECTOR 8500", "implementadora": "RANDON"},
        {"estado": "RJ", "segmento": "TRAILER", "linha": "VECTOR 8500"},
    ])

    regional = engine.regional_analysis()
    assert {item["estado"] for item in regional} == {"SP", "RJ"}

    diagnostico = engine.diagnostico_estrategico()
    assert diagnostico["total_faturamento"] == 356000

    share = engine.oem_share()
    assert share == [{"implementadora": "RANDON", "valor": 178000, "share": 100.0}]

    dominance = engine.market_dominance()
    assert dominance == [{"implementadora": "RANDON", "valor": 178000, "dominancia": 100.0}]
