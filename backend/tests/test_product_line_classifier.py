from services.product_line_classifier import classificar_linha, modelo_linha


def test_classifica_modelos_oficiais_tr():
    assert classificar_linha({"modelo_equipamento": "X4-7500"}) == "TR"
    assert classificar_linha({"produto": "X4 7700"}) == "TR"
    assert classificar_linha({"modelo_carrier": "Vector HE19"}) == "TR"
    assert modelo_linha({"modelo": "X47500"}) == "X4-7500"


def test_classifica_modelos_oficiais_dt():
    assert classificar_linha({"tipo_equipamento": "Supra 750"}) == "DT"
    assert classificar_linha({"equipamento": "Supra 850"}) == "DT"
    assert classificar_linha({"modelo_carrier": "Supra1150"}) == "DT"
    assert modelo_linha({"modelo": "SUPRA850"}) == "SUPRA 850"


def test_classifica_modelos_oficiais_dd():
    modelos = {
        "CM 280": "CM280",
        "CM400": "CM400",
        "CM-500": "CM500",
        "CM 500 AE": "CM500AE",
        "D6": "D6",
        "D6 AE": "D6AE",
        "D7": "D7",
        "D7AE": "D7AE",
        "Xarios350": "XARIOS 350",
        "Xarios 600": "XARIOS 600",
    }
    for informado, canonico in modelos.items():
        registro = {"modelo_equipamento": informado}
        assert classificar_linha(registro) == "DD"
        assert modelo_linha(registro) == canonico


def test_tipo_de_veiculo_nao_determina_linha_de_produto():
    for tipo_veiculo in (
        "Caminhão", "Truck", "Van", "Furgão", "VUC",
        "Carreta", "Semi-reboque frigorífico",
    ):
        assert classificar_linha({"tipo_veiculo": tipo_veiculo}) is None
        assert modelo_linha({"tipo_veiculo": tipo_veiculo}) == "NÃO INFORMADO"


def test_linha_explicita_determina_classificacao_sem_inventar_modelo():
    assert classificar_linha({"linha": "TR - Trailer"}) == "TR"
    assert classificar_linha({"linha": "Diesel Truck"}) == "DT"
    assert classificar_linha({"linha": "Direct Drive"}) == "DD"
    assert modelo_linha({"linha": "Direct Drive"}) == "NÃO INFORMADO"


def test_modelos_nao_oficiais_nao_sao_inferidos():
    assert classificar_linha({"modelo": "Citimax 500"}) is None
    assert classificar_linha({"modelo": "CM600"}) is None
    assert classificar_linha({"modelo": "Xarios 6"}) is None


def test_nao_forca_classificacao_sem_evidencia_do_equipamento():
    assert classificar_linha({"tipo_veiculo": "Não informado"}) is None
    assert classificar_linha({"fabricante_caminhao": "Volvo", "modelo_caminhao": "FH"}) is None
