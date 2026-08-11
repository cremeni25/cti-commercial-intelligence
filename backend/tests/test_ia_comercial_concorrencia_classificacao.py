from services import ia_comercial_sintese_factual as sintese


def test_classificacao_fabricantes_separa_proprio_concorrentes_e_ruido():
    ranking = [
        {"valor": "THERMOKING", "registros": 34},
        {"valor": "THERMOFLEX", "registros": 32},
        {"valor": "THERMOSTAR", "registros": 22},
        {"valor": "CARRRIER", "registros": 18},
        {"valor": "DOCUMENTAÇÃO", "registros": 10},
        {"valor": "RODOFRIO", "registros": 10},
        {"valor": "PALÁCIO", "registros": 2},
    ]

    resultado = sintese._classificar_fabricantes_equipamento(ranking)

    assert resultado["proprio"] == [
        {"valor": "CARRRIER", "registros": 18, "fabricante_canonico": "CARRIER"}
    ]
    assert [item["valor"] for item in resultado["concorrentes"]] == [
        "THERMOKING",
        "THERMOFLEX",
        "THERMOSTAR",
        "RODOFRIO",
        "PALÁCIO",
    ]
    assert [item["registros"] for item in resultado["concorrentes"]] == [34, 32, 22, 10, 2]
    assert [item["valor"] for item in resultado["valores_nao_fabricante"]] == [
        "DOCUMENTAÇÃO",
    ]
    assert resultado["nao_classificados"] == []


def test_resumo_concorrencia_expoe_classificacao_sem_ranking_bruto():
    resultado = {
        "total_encontrado": 588,
        "resumo": {
            "total_registros": 588,
            "total_clientes": 100,
            "ranking_implementadoras": [],
            "relacoes_implementadoras": [],
            "ranking_fabricantes_equipamento": [
                {"valor": "CARRRIER", "registros": 18},
                {"valor": "THERMOKING", "registros": 34},
                {"valor": "DOCUMENTAÇÃO", "registros": 10},
                {"valor": "PALÁCIO", "registros": 2},
            ],
            "ranking_linhas": [],
        },
    }

    resumo = sintese._resumo_territorial_relevante(
        resultado,
        "Quais implementadoras aparecem no DDD 011 e onde existem sinais de fabricantes concorrentes?",
    )

    assert "ranking_fabricantes_equipamento" not in resumo
    classificacao = resumo["classificacao_fabricantes_equipamento"]
    assert classificacao["proprio"][0]["fabricante_canonico"] == "CARRIER"
    assert [item["valor"] for item in classificacao["concorrentes"]] == ["THERMOKING", "PALÁCIO"]
    assert classificacao["valores_nao_fabricante"][0]["valor"] == "DOCUMENTAÇÃO"


def test_instrucao_proibe_carrier_como_concorrente_e_reconhece_palacio():
    instrucoes = sintese.INSTRUCOES_SINTESE_FATUAL
    assert "NUNCA pode ser chamado de concorrente" in instrucoes
    assert "SOMENTE classificacao_fabricantes_equipamento.concorrentes" in instrucoes
    assert "Palácio é fabricante concorrente" in instrucoes
