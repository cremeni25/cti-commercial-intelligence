from services.anfir_market_scope import implementadora_fora_escopo, particionar_mercado_disputavel


def _r(implementadora: str) -> dict:
    return {"implementadora": implementadora}


def test_identifica_somente_implementadoras_fora_do_escopo_autorizadas():
    assert implementadora_fora_escopo(_r("Fibra West Comércio de Carrocerias Ltda")) == "FIBRA WEST"
    assert implementadora_fora_escopo(_r("HI FLEX")) == "HIFLEX"
    assert implementadora_fora_escopo(_r("Hiflex")) == "HIFLEX"
    assert implementadora_fora_escopo(_r("Planalto Carrocerias")) == "PLANALTO"
    assert implementadora_fora_escopo(_r("Fibra Vest")) is None
    assert implementadora_fora_escopo(_r("Fibrasil")) is None


def test_particionamento_preserva_total_e_recalcula_denominador_comercial():
    registros = [
        _r("Fibra West"),
        _r("Fibra West Comércio de Carrocerias Ltda"),
        _r("HiFlex"),
        _r("Planalto"),
        _r("Ibiporã"),
        _r("Facchini"),
    ]
    disputavel, fora, resumo = particionar_mercado_disputavel(registros)

    assert len(disputavel) == 2
    assert len(fora) == 4
    assert resumo["mercado_anfir_total"] == 6
    assert resumo["mercado_fora_escopo_comercial"] == 4
    assert resumo["mercado_disputavel_viena"] == 2
    assert resumo["mercado_anfir_total"] == resumo["mercado_fora_escopo_comercial"] + resumo["mercado_disputavel_viena"]
    assert resumo["percentual_fora_escopo"] == 66.67
    assert resumo["percentual_disputavel"] == 33.33


def test_resumo_mantem_tres_blocos_mesmo_sem_ocorrencia_na_fonte():
    _, _, resumo = particionar_mercado_disputavel([_r("Fibra West"), _r("Facchini")])
    por_nome = {item["implementadora"]: item["registros"] for item in resumo["implementadoras_fora_escopo"]}

    assert por_nome == {"FIBRA WEST": 1, "HIFLEX": 0, "PLANALTO": 0}
