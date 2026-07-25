from services.product_line_classifier import classificar_linha, modelo_linha


def test_classifica_linhas_por_modelos_e_campos_de_equipamento():
    assert classificar_linha({"modelo_equipamento": "Vector HE19"}) == "TR"
    assert classificar_linha({"produto": "X4 7700"}) == "TR"
    assert classificar_linha({"tipo_equipamento": "Supra 850"}) == "DT"
    assert classificar_linha({"equipamento": "Citimax 500"}) == "DD"
    assert classificar_linha({"descricao": "Unidade Direct Drive Xarios 6"}) == "DD"
    assert classificar_linha({"modelo_carrier": "CM 600"}) == "DD"


def test_tipo_de_veiculo_nao_determina_linha_de_produto():
    for tipo_veiculo in (
        "Caminhão", "Truck", "Van", "Furgão", "VUC",
        "Carreta", "Semi-reboque frigorífico",
    ):
        assert classificar_linha({"tipo_veiculo": tipo_veiculo}) is None


def test_linha_e_modelo_de_equipamento_determinam_classificacao():
    assert classificar_linha({"linha": "TR - Trailer", "modelo": "não informado"}) == "TR"
    assert classificar_linha({"linha": "Diesel Truck", "modelo": "não informado"}) == "DT"
    assert classificar_linha({"linha": "Direct Drive", "modelo": "não informado"}) == "DD"
    assert classificar_linha({"linha_produto": "Unidade Diesel Truck"}) == "DT"
    assert classificar_linha({"familia": "Acoplado ao motor"}) == "DD"


def test_nao_confunde_tr_com_truck():
    assert classificar_linha({"linha": "Diesel Truck"}) == "DT"


def test_nao_exibe_tipo_de_veiculo_como_modelo_do_equipamento():
    assert modelo_linha({"tipo_veiculo": "Caminhão"}) == "NÃO INFORMADO"
    assert modelo_linha({"modelo_carrier": "Supra 850", "tipo_veiculo": "Caminhão"}) == "Supra 850"


def test_nao_forca_classificacao_sem_evidencia_do_equipamento():
    assert classificar_linha({"tipo_veiculo": "Não informado"}) is None
    assert classificar_linha({"fabricante_caminhao": "Volvo", "modelo_caminhao": "FH"}) is None
