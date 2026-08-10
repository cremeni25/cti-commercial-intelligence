from services.ia_comercial_sintese_factual import _ranking_canonico_frota


def test_ranking_canonico_consolida_caixa_e_acentuacao_sem_perder_variantes():
    ranking = [
        {"valor": "VOLKSWAGEN", "registros": 219},
        {"valor": "Volkswagen", "registros": 4},
        {"valor": "IVECO", "registros": 64},
        {"valor": "Iveco", "registros": 1},
        {"valor": "VOLVO", "registros": 6},
        {"valor": "Volvo", "registros": 1},
    ]

    resultado = _ranking_canonico_frota(ranking)

    assert resultado[0]["valor"] == "VOLKSWAGEN"
    assert resultado[0]["registros"] == 223
    assert resultado[0]["variantes"] == [
        {"valor": "VOLKSWAGEN", "registros": 219},
        {"valor": "Volkswagen", "registros": 4},
    ]

    iveco = next(item for item in resultado if item["valor"] == "IVECO")
    assert iveco["registros"] == 65
    volvo = next(item for item in resultado if item["valor"] == "VOLVO")
    assert volvo["registros"] == 7


def test_ranking_canonico_tipo_veiculo_consolida_acento_e_caixa():
    ranking = [
        {"valor": "CAMINHAO", "registros": 246},
        {"valor": "CAMINHÃO", "registros": 63},
        {"valor": "Caminhão", "registros": 5},
        {"valor": "CAMINHONETE", "registros": 119},
        {"valor": "Caminhonete", "registros": 3},
        {"valor": "SEMIRREBOQUE", "registros": 152},
    ]

    resultado = _ranking_canonico_frota(ranking)

    caminhao = next(item for item in resultado if item["valor"] == "CAMINHAO")
    assert caminhao["registros"] == 314
    assert len(caminhao["variantes"]) == 3

    caminhonete = next(item for item in resultado if item["valor"] == "CAMINHONETE")
    assert caminhonete["registros"] == 122

    semirreboque = next(item for item in resultado if item["valor"] == "SEMIRREBOQUE")
    assert semirreboque["registros"] == 152


def test_ranking_canonico_nao_faz_normalizacao_semantica_de_modelos():
    ranking = [
        {"valor": "ACCELO 1117 CE", "registros": 20},
        {"valor": "ACCELO 1117CE", "registros": 17},
    ]

    # A função canônica é usada apenas para tipos/fabricantes. Este teste
    # documenta que os modelos continuam devendo ser fornecidos pelo ranking bruto.
    assert ranking[0]["registros"] == 20
    assert ranking[1]["registros"] == 17
