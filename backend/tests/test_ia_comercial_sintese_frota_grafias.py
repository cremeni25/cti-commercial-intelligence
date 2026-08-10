from services import ia_comercial_sintese_factual as sintese


def test_sintese_frota_nao_agrega_variacoes_de_grafia_sem_backend():
    instrucoes = sintese.INSTRUCOES_SINTESE_FATUAL.casefold()

    assert "não some, normalize, una" in instrucoes
    assert "inclui variações de grafia" in instrucoes
    assert "apresente-as separadamente" in instrucoes


def test_resumo_frota_declara_regra_de_rankings_brutos():
    resultado = {
        "resumo": {
            "total_registros": 2,
            "total_clientes": 1,
            "total_veiculos_identificaveis": 1,
            "registros_sem_identificador_veiculo": 0,
            "cobertura": {
                "com_placa": 2,
                "sem_placa": 0,
                "com_chassi": 2,
                "sem_chassi": 0,
                "com_numero_frota": 0,
                "sem_numero_frota": 2,
                "com_fabricante_caminhao": 2,
                "sem_fabricante_caminhao": 0,
                "com_modelo_caminhao": 2,
                "sem_modelo_caminhao": 0,
            },
            "ranking_tipos_veiculo": [],
            "ranking_fabricantes_caminhao": [
                {"valor": "VOLKSWAGEN", "registros": 1},
                {"valor": "Volkswagen", "registros": 1},
            ],
            "ranking_modelos_caminhao": [],
        }
    }

    resumo = sintese._resumo_territorial_relevante(
        resultado,
        "Analise a frota no DDD 011 e os fabricantes de caminhão.",
    )

    assert resumo["frota"]["ranking_fabricantes_caminhao_por_registros"] == [
        {"valor": "VOLKSWAGEN", "registros": 1},
        {"valor": "Volkswagen", "registros": 1},
    ]
    assert "não agregar variações" in resumo["frota"]["regra_rankings"]
