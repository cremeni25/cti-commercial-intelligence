from services.cnpj_enrichment_service import cnpj_valido, normalizar_empresa, somente_digitos


def test_somente_digitos_normaliza_cnpj_formatado():
    assert somente_digitos("00.000.000/0001-91") == "00000000000191"


def test_validador_aceita_cnpj_valido_e_recusa_repetido():
    assert cnpj_valido("00.000.000/0001-91") is True
    assert cnpj_valido("11.111.111/1111-11") is False
    assert cnpj_valido("123") is False


def test_normalizacao_mapeia_ficha_cadastral_sem_inventar_campos():
    payload = {
        "razao_social": "EMPRESA TESTE SA",
        "nome_fantasia": "EMPRESA TESTE",
        "descricao_situacao_cadastral": "ATIVA",
        "logradouro": "RUA EXEMPLO",
        "numero": "123",
        "complemento": "SALA 1",
        "bairro": "CENTRO",
        "municipio": "SAO PAULO",
        "uf": "SP",
        "cep": "01001-000",
        "ddd_telefone_1": "1133334444",
        "email": "CADASTRO@EXEMPLO.COM",
        "cnae_fiscal": 4930202,
        "cnae_fiscal_descricao": "Transporte rodoviário de carga",
    }
    dados = normalizar_empresa(payload, "00000000000191")
    assert dados["nome"] == "EMPRESA TESTE SA"
    assert dados["estado"] == "SP"
    assert dados["cep"] == "01001000"
    assert dados["ddd"] == "11"
    assert dados["email"] == "cadastro@exemplo.com"
    assert dados["situacao_cadastral"] == "ATIVA"
    assert dados["fonte"] == "BrasilAPI / Minha Receita"
