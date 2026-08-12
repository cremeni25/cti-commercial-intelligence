from services import ia_comercial_sintese_factual as sintese
from services import ia_comercial_territorio_anfir as territorio


def test_resumo_frota_distingue_registros_de_veiculos_identificaveis():
    registros = [
        {
            "cliente": "CLIENTE A",
            "ddd": "011",
            "chassi": "CHASSI-1",
            "placa": "AAA1A11",
            "tipo_veiculo": "CAMINHAO",
            "fabricante_caminhao": "VOLKSWAGEN",
            "modelo_caminhao": "9.160",
        },
        {
            "cliente": "CLIENTE A",
            "ddd": "011",
            "chassi": "CHASSI-1",
            "placa": "AAA1A11",
            "tipo_veiculo": "CAMINHAO",
            "fabricante_caminhao": "VOLKSWAGEN",
            "modelo_caminhao": "9.160",
        },
        {
            "cliente": "CLIENTE B",
            "ddd": "011",
            "chassi": None,
            "placa": "BBB2B22",
            "tipo_veiculo": "SEMIRREBOQUE",
            "fabricante_caminhao": None,
            "modelo_caminhao": None,
        },
        {
            "cliente": "CLIENTE C",
            "ddd": "011",
            "chassi": None,
            "placa": None,
            "id_operacional": None,
            "tipo_veiculo": "CAMINHAO",
        },
    ]

    resumo = territorio._resumir(registros)

    assert resumo["total_registros"] == 4
    assert resumo["total_veiculos_identificaveis"] == 2
    assert resumo["registros_sem_identificador_veiculo"] == 1
    assert resumo["cobertura"]["com_chassi"] == 2
    assert resumo["cobertura"]["sem_chassi"] == 2
    assert resumo["cobertura"]["com_placa"] == 3
    assert resumo["cobertura"]["sem_placa"] == 1
    assert resumo["ranking_tipos_veiculo"] == [
        {"valor": "CAMINHAO", "registros": 3},
        {"valor": "SEMIRREBOQUE", "registros": 1},
    ]
    assert resumo["ranking_fabricantes_caminhao"] == [
        {"valor": "VOLKSWAGEN", "registros": 2}
    ]


def test_registro_publico_expoe_identificacao_e_composicao_de_frota_autorizada():
    registro = territorio._registro_publico(
        {
            "cliente": "CLIENTE A",
            "ddd": "11",
            "placa": "AAA1A11",
            "chassi": "CHASSI-1",
            "numero_frota": "F-10",
            "fabricante_caminhao": "IVECO",
            "modelo_caminhao": "DAILY",
            "eixo": "4X2",
            "tipo_veiculo": "CAMINHAO",
            "linha": "DT",
        }
    )

    assert registro["ddd"] == "011"
    assert registro["placa"] == "AAA1A11"
    assert registro["chassi"] == "CHASSI-1"
    assert registro["numero_frota"] == "F-10"
    assert registro["fabricante_caminhao"] == "IVECO"
    assert registro["modelo_caminhao"] == "DAILY"
    assert registro["tipo_veiculo"] == "CAMINHAO"


def test_sintese_so_inclui_frota_quando_pergunta_pede_dimensao_de_frota():
    resultado = {
        "fonte": "cti_anfir",
        "visao": "territorio",
        "total_encontrado": 4,
        "resumo": {
            "total_registros": 4,
            "total_clientes": 3,
            "total_veiculos_identificaveis": 2,
            "registros_sem_identificador_veiculo": 1,
            "cobertura": {
                "com_placa": 3,
                "sem_placa": 1,
                "com_chassi": 2,
                "sem_chassi": 2,
                "com_numero_frota": 1,
                "sem_numero_frota": 3,
                "com_fabricante_caminhao": 2,
                "sem_fabricante_caminhao": 2,
                "com_modelo_caminhao": 2,
                "sem_modelo_caminhao": 2,
            },
            "ranking_tipos_veiculo": [{"valor": "CAMINHAO", "registros": 3}],
            "ranking_fabricantes_caminhao": [{"valor": "VOLKSWAGEN", "registros": 2}],
            "ranking_modelos_caminhao": [{"valor": "9.160", "registros": 2}],
        },
    }

    com_frota = sintese._resumo_territorial_relevante(
        resultado,
        "Analise a frota e os veículos do DDD 011, incluindo placa, chassi e fabricantes de caminhão.",
    )
    sem_frota = sintese._resumo_territorial_relevante(
        resultado,
        "Mostre apenas a concentração territorial no DDD 011.",
    )

    assert "frota" in com_frota
    assert com_frota["frota"]["total_veiculos_identificaveis"] == 2
    assert com_frota["frota"]["cobertura_identificacao"]["com_placa"] == 3
    assert "frota" not in sem_frota


def test_instrucoes_frota_proibem_confundir_registros_com_veiculos_unicos():
    instrucoes = sintese.INSTRUCOES_SINTESE_FATUAL.casefold()

    assert "diferencie obrigatoriamente total_registros de total_veiculos_identificaveis" in instrucoes
    assert "um mesmo veículo pode aparecer em mais de um registro histórico" in instrucoes
    assert "não os apresente como contagem de veículos únicos" in instrucoes
