from services import ia_comercial_sintese_factual as sintese


def test_sintese_frota_usa_agregado_backend_sem_reagrupar_modelos():
    instrucoes = sintese.INSTRUCOES_SINTESE_FATUAL.casefold()

    assert "ranking_canônico fornecido pelo backend" in instrucoes
    assert "não refaça somas nem crie agrupamentos adicionais" in instrucoes
    assert "para modelos de caminhão" in instrucoes
    assert "não some variantes por conta própria" in instrucoes


def test_resumo_frota_usa_agregados_backend_e_preserva_variantes():
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
            "ranking_modelos_caminhao": [
                {"valor": "ACCELO 1117 CE", "registros": 1},
                {"valor": "ACCELO 1117CE", "registros": 1},
            ],
        }
    }

    resumo = sintese._resumo_territorial_relevante(
        resultado,
        "Analise a frota no DDD 011 e os fabricantes e modelos de caminhão.",
    )

    fabricantes = resumo["frota"]["ranking_fabricantes_caminhao_canonico_por_registros"]
    assert fabricantes == [
        {
            "valor": "VOLKSWAGEN",
            "registros": 2,
            "variantes": [
                {"valor": "VOLKSWAGEN", "registros": 1},
                {"valor": "Volkswagen", "registros": 1},
            ],
            "regra_agregacao": "mesma categoria após normalização determinística de caixa, acentuação e pontuação",
        }
    ]
    assert resumo["frota"]["ranking_modelos_caminhao_por_registros"] == [
        {"valor": "ACCELO 1117 CE", "registros": 1},
        {"valor": "ACCELO 1117CE", "registros": 1},
    ]
    assert "backend" in resumo["frota"]["regra_rankings"].casefold()
