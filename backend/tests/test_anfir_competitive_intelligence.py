from services.anfir_competitive_intelligence import consolidar_competitividade_anfir_2026


def _r(data, linha, fabricante="", ocorrencia="", cliente="Cliente", status="", motivo=""):
    return {
        "id": f"{data}-{linha}-{fabricante}-{cliente}",
        "data_venda": data,
        "ano": 2026,
        "mes": int(data[5:7]),
        "linha": linha,
        "fabricante_equipamento": fabricante,
        "ocorrencia": ocorrencia,
        "status": status,
        "motivo": motivo,
        "cliente": cliente,
        "estado": "SP",
        "cidade": "SAO PAULO",
        "ddd": "11",
    }


def test_competitividade_usa_taxonomia_e_normaliza_aliases():
    registros = [
        _r("2026-01-10", "TR", "CARRRIER"),
        _r("2026-01-11", "TR", "THERMOKING"),
        _r("2026-01-12", "TR", "PALÁCIO"),
        _r("2026-01-13", "TR", "", "fabricante Thermoflex"),
    ]
    payload = consolidar_competitividade_anfir_2026(
        registros,
        ["CARRIER", "THERMOKING", "PALACIO", "THERMOFLEX"],
    )
    trailer = next(s for s in payload["segmentos"] if s["codigo"] == "TR")
    assert trailer["carrier"] == 1
    assert trailer["concorrencia"] == 3
    assert {x["fabricante"] for x in trailer["fabricantes_concorrentes"]} == {"THERMOKING", "PALACIO", "THERMOFLEX"}
    assert not any(x["fabricante"] == "CARRIER" for x in payload["ranking_concorrentes"])


def test_documentacao_e_reaproveitamento_nao_fabricante():
    payload = consolidar_competitividade_anfir_2026(
        [_r("2026-02-10", "DT", "DOCUMENTAÇÃO", "regularização documental FWest")],
        ["CARRIER", "THERMOKING"],
    )
    diesel = next(s for s in payload["segmentos"] if s["codigo"] == "DT")
    assert diesel["reaproveitamento_documentacao"] == 1
    assert diesel["concorrencia"] == 0
    assert diesel["carrier"] == 0
    assert payload["detalhes"][0]["grupo"] == "REAPROVEITAMENTO"
    assert "não é fabricante" in payload["metadata"]["regra_documentacao"]


def test_segmentos_tem_evolucao_mensal_carrier_concorrencia():
    payload = consolidar_competitividade_anfir_2026(
        [
            _r("2026-03-01", "DD", "CARRIER"),
            _r("2026-03-02", "DD", "THERMOFLEX"),
            _r("2026-04-01", "DD", "THERMOFLEX"),
        ],
        ["CARRIER", "THERMOFLEX"],
    )
    dd = next(s for s in payload["segmentos"] if s["codigo"] == "DD")
    assert dd["mensal"][0]["carrier"] == 1
    assert dd["mensal"][0]["concorrencia"] == 1
    assert dd["mensal"][1]["carrier"] == 0
    assert dd["mensal"][1]["concorrencia"] == 1


def test_mencao_historica_a_carrier_na_observacao_nao_vira_venda_carrier():
    payload = consolidar_competitividade_anfir_2026(
        [_r("2026-05-01", "DT", "", "Cliente possui Carrier, mas está testando pós-venda e custos de outra empresa")],
        ["CARRIER", "THERMOFLEX"],
    )
    dt = next(s for s in payload["segmentos"] if s["codigo"] == "DT")
    assert dt["carrier"] == 0
    assert dt["a_identificar"] == 1


def test_carrier_pode_ser_recuperada_de_status_estruturado():
    payload = consolidar_competitividade_anfir_2026(
        [_r("2026-06-01", "TR", "", status="Carrier", motivo="CARRIER")],
        ["CARRIER", "THERMOKING"],
    )
    tr = next(s for s in payload["segmentos"] if s["codigo"] == "TR")
    assert tr["carrier"] == 1
