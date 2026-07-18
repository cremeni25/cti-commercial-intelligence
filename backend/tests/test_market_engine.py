from engine.market_engine import MarketEngine


def test_market_engine_usa_implementadora_do_dominio_sem_keyerror():
    engine = MarketEngine([
        {
            "estado": "SP",
            "segmento": "TRAILER",
            "linha": "VECTOR 8500",
            "implementadora": "PAVAN",
            "origem_base": "BRASIL",
        },
        {
            "estado": "SP",
            "segmento": "TRAILER",
            "linha": "VECTOR 8500",
            "implementadora": "RANDON",
            "origem_base": "VIENA_SP",
            "autorizado": "VIENA",
        },
        {
            "estado": "RJ",
            "segmento": "TRAILER",
            "linha": "VECTOR 8500",
            "origem_base": "BRASIL",
        },
    ])

    resultado = engine.market_intelligence()

    assert resultado["market_dominance"]
    assert {item["implementadora"] for item in resultado["market_dominance"]} == {"PAVAN", "RANDON"}
    assert {item["implementadora"] for item in resultado["oem_share"]} == {"PAVAN", "RANDON"}
