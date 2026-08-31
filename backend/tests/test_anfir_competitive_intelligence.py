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


def test_status_oficial_domina_market_share_e_texto_nao_inventa_fabricante():
    registros = [
        _r("2026-01-10", "TR", "CARRRIER", status="CARRIER"),
        _r("2026-01-11", "TR", "", status="TK"),
        _r("2026-01-12", "TR", "", ocorrencia="cliente possui TK historicamente", status="SEMCONTATO"),
    ]
    payload = consolidar_competitividade_anfir_2026(registros, ["CARRIER", "THERMOKING"])
    trailer = next(s for s in payload["segmentos"] if s["codigo"] == "TR")
    assert trailer["carrier"] == 1
    assert trailer["thermoking"] == 1
    assert trailer["concorrencia"] == 1
    assert trailer["sem_contato"] == 1
    assert trailer["a_identificar"] == 0


def test_tk_e_contada_pelo_status_mesmo_sem_fabricante_auxiliar():
    payload = consolidar_competitividade_anfir_2026(
        [_r("2026-03-01", "TR", "", status="TK", ocorrencia="cliente optou por TK")],
        ["CARRIER", "THERMOKING"],
    )
    tr = next(s for s in payload["segmentos"] if s["codigo"] == "TR")
    assert tr["thermoking"] == 1
    assert payload["ranking_concorrentes"][0]["fabricante"] == "THERMOKING"


def test_nacional_entra_como_concorrencia_sem_inventar_marca():
    payload = consolidar_competitividade_anfir_2026(
        [
            _r("2026-04-01", "DD", "THERMOFLEX", status="NACIONAL"),
            _r("2026-04-02", "DD", "", status="NACIONAL", ocorrencia="marca não informada"),
        ],
        ["CARRIER", "THERMOKING", "THERMOFLEX"],
    )
    dd = next(s for s in payload["segmentos"] if s["codigo"] == "DD")
    assert dd["concorrencia"] == 2
    assert dd["nacional"] == 2
    assert dd["nacional_fabricante_nao_identificado"] == 1
    assert dd["fabricantes_concorrentes"] == [{"fabricante": "THERMOFLEX", "registros": 1, "percentual_mercado": 50.0}]


def test_usados_nao_inflam_concorrencia_de_equipamento_novo():
    payload = consolidar_competitividade_anfir_2026(
        [
            _r("2026-05-01", "DT", status="USADOCONCORRENTE", ocorrencia="equipamento usado TK"),
            _r("2026-05-02", "DT", status="USADOCARRIER"),
        ],
        ["CARRIER", "THERMOKING"],
    )
    dt = next(s for s in payload["segmentos"] if s["codigo"] == "DT")
    assert dt["concorrencia"] == 0
    assert dt["usado_concorrente"] == 1
    assert dt["usado_carrier"] == 1


def test_documentacao_e_reaproveitamento_nao_fabricante():
    payload = consolidar_competitividade_anfir_2026(
        [_r("2026-02-10", "DT", "DOCUMENTAÇÃO", "regularização documental FWest", status="USADOCONCORRENTE")],
        ["CARRIER", "THERMOKING"],
    )
    diesel = next(s for s in payload["segmentos"] if s["codigo"] == "DT")
    assert diesel["reaproveitamento_documentacao"] == 1
    assert diesel["concorrencia"] == 0
    assert diesel["carrier"] == 0
    assert payload["detalhes"][0]["grupo"] == "REAPROVEITAMENTO_DOCUMENTACAO"
    assert "não é fabricante" in payload["metadata"]["regra_documentacao"]


def test_segmentos_tem_evolucao_mensal_carrier_concorrencia_e_tk():
    payload = consolidar_competitividade_anfir_2026(
        [
            _r("2026-03-01", "DD", status="CARRIER"),
            _r("2026-03-02", "DD", status="TK"),
            _r("2026-04-01", "DD", "THERMOFLEX", status="NACIONAL"),
        ],
        ["CARRIER", "THERMOKING", "THERMOFLEX"],
    )
    dd = next(s for s in payload["segmentos"] if s["codigo"] == "DD")
    assert dd["mensal"][0]["carrier"] == 1
    assert dd["mensal"][0]["concorrencia"] == 1
    assert dd["mensal"][0]["thermoking"] == 1
    assert dd["mensal"][1]["carrier"] == 0
    assert dd["mensal"][1]["concorrencia"] == 1
    assert dd["mensal"][1]["nacional"] == 1
