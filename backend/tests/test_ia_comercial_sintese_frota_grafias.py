from services import ia_comercial_sintese_factual as sintese


def test_sintese_frota_proibe_agregacao_livre_e_aceita_agregado_backend():
    instrucoes = sintese.INSTRUCOES_SINTESE_FATUAL.casefold()

    assert "não some, normalize ou una categorias brutas por conta própria" in instrucoes
    assert "agregados canônicos fornecidos pelo backend" in instrucoes
    assert "modelos de caminhão permanecem separados" in instrucoes


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
            "valor_canonico": "VOLKSWAGEN",
            "registros": 2,
            "variantes": [
                {"valor": "VOLKSWAGEN", "registros": 1},
                {"valor": "Volkswagen", "registros": 1},
            ],
        }
    ]
    assert resumo["frota"]["ranking_modelos_caminhao_por_registros"] == [
        {"valor": "ACCELO 1117 CE", "registros": 1},
        {"valor": "ACCELO 1117CE", "registros": 1},
    ]
    assert "backend" in resumo["frota"]["regra_rankings"].casefold()
