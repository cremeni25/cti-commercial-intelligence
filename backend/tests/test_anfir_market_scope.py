from services.anfir_market_scope import implementadora_fora_escopo, particionar_mercado_disputavel


def _r(implementadora: str, mes: int = 1, linha: str = "Direct Drive") -> dict:
    return {"implementadora": implementadora, "ano_referencia": 2026, "mes": mes, "linha": linha}


def test_identifica_somente_implementadoras_fora_do_escopo_autorizadas():
    assert implementadora_fora_escopo(_r("Fibra West Comércio de Carrocerias Ltda")) == "FIBRA WEST"
    assert implementadora_fora_escopo(_r("HIGH FLEX")) == "HIGH FLEX"
    assert implementadora_fora_escopo(_r("HIGH FLEX INDÚSTRIA E COMÉRCIO")) == "HIGH FLEX"
    assert implementadora_fora_escopo(_r("HI FLEX")) == "HIGH FLEX"
    assert implementadora_fora_escopo(_r("Hiflex")) == "HIGH FLEX"
    assert implementadora_fora_escopo(_r("Planalto Carrocerias")) == "PLANALTO"
    assert implementadora_fora_escopo(_r("Fibra Vest")) is None
    assert implementadora_fora_escopo(_r("Fibrasil")) is None


def test_particionamento_preserva_total_e_recalcula_denominador_comercial():
    registros = [
        _r("Fibra West"),
        _r("Fibra West Comércio de Carrocerias Ltda"),
        _r("High Flex"),
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

    assert por_nome == {"FIBRA WEST": 1, "HIGH FLEX": 0, "PLANALTO": 0}


def test_comparativos_mensal_e_segmento_fecham_total_menos_abate_igual_real():
    registros = [
        _r("High Flex", mes=1, linha="Direct Drive"),
        _r("Fibra West", mes=1, linha="Direct Drive"),
        _r("Ibiporã", mes=1, linha="Direct Drive"),
        _r("Facchini", mes=2, linha="Trailer"),
    ]
    _, _, resumo = particionar_mercado_disputavel(registros)
    janeiro = next(item for item in resumo["comparativo_mensal"] if item["competencia"] == "2026-01")
    direct_drive = next(item for item in resumo["comparativo_segmentos"] if item["codigo"] == "DD")

    assert janeiro == {"mes": "Janeiro", "competencia": "2026-01", "mercado_total": 3, "mercado_excluido": 2, "mercado_real": 1}
    assert direct_drive["mercado_total"] == 3
    assert direct_drive["mercado_excluido"] == 2
    assert direct_drive["mercado_real"] == 1
