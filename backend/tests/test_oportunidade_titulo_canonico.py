from routers import clientes_oportunidade_router as clientes


def test_titulo_canonico_prioriza_tipo_da_oportunidade():
    descricao = "Tipo da oportunidade: Cotação / tomada de preços\nObservação: cliente solicitou condição comercial."
    assert clientes._titulo_canonico("CITIMAX 400 • PINEX LOGISTIC SOLUTION LTDA", descricao) == "Cotação / tomada de preços"


def test_titulo_canonico_rejeita_rotulo_documental_como_identidade():
    assert clientes._titulo_canonico("Proposta Comercial", "Negociação em andamento") == "Oportunidade comercial"


def test_titulo_canonico_preserva_intencao_comercial_legitima_sem_tipo_estruturado():
    assert clientes._titulo_canonico("Renovação de frota", None) == "Renovação de frota"
