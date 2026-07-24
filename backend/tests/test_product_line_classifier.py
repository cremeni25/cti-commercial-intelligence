from services.product_line_classifier import classificar_linha


def test_classifica_linhas_por_modelos_e_campos_alternativos():
    assert classificar_linha({"modelo_equipamento": "Vector HE19"}) == "TR"
    assert classificar_linha({"produto": "X4 7700"}) == "TR"
    assert classificar_linha({"tipo_equipamento": "Supra 850"}) == "DT"
    assert classificar_linha({"equipamento": "Citimax 500"}) == "DD"
    assert classificar_linha({"descricao": "Unidade Direct Drive Xarios 6"}) == "DD"


def test_classifica_linhas_por_nomenclatura_veicular_nacional():
    assert classificar_linha({"tipo_veiculo": "Semi-reboque frigorífico"}) == "TR"
    assert classificar_linha({"linha_produto": "Unidade Diesel Truck"}) == "DT"
    assert classificar_linha({"familia": "Acoplado ao motor"}) == "DD"


def test_nao_forca_classificacao_sem_evidencia():
    assert classificar_linha({"tipo_veiculo": "Não informado"}) is None
