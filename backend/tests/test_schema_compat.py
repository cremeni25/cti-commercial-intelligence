from backend.services.schema_compat import missing_column_from_error


def test_extrai_coluna_pgrst204():
    erro = Exception("{'message': \"Could not find the 'equipamento' column of 'cti_oportunidades' in the schema cache\", 'code': 'PGRST204'}")
    assert missing_column_from_error(erro) == "equipamento"


def test_nao_inventa_coluna_em_erro_generico():
    assert missing_column_from_error(Exception("falha de conexão")) is None
