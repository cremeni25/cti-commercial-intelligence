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
