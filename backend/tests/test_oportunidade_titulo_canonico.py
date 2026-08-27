from routers import clientes_oportunidade_router as clientes


def test_titulo_canonico_preserva_assunto_comercial_mesmo_com_tipo_estruturado():
    descricao = "Tipo da oportunidade: Prospecção comercial\nObservação: cliente solicitou condição comercial."
    assert clientes._titulo_canonico("Tomada de Preços", descricao) == "Tomada de Preços"


def test_titulo_canonico_generico_usa_tipo_da_oportunidade():
    descricao = "Tipo da oportunidade: Cotação / tomada de preços\nObservação: cliente solicitou condição comercial."
    assert clientes._titulo_canonico("Proposta Comercial", descricao) == "Cotação / tomada de preços"


def test_titulo_canonico_rejeita_rotulo_documental_sem_tipo_como_identidade():
    assert clientes._titulo_canonico("Proposta Comercial", "Negociação em andamento") == "Oportunidade comercial"


def test_titulo_canonico_preserva_intencao_comercial_legitima_sem_tipo_estruturado():
    assert clientes._titulo_canonico("Renovação de frota", None) == "Renovação de frota"


def test_descricao_com_contexto_remove_bloco_anterior_e_grava_um_unico_contexto():
    descricao = "Tipo da oportunidade: Cotação / tomada de preços\nObservação comercial\n[CONTEXTO CTI]\nequipamentos: CITIMAX 400\n[CONTEXTO CTI]\nequipamentos: ANTIGO"
    resultado = clientes._descricao_com_contexto(descricao, {"equipamentos": "CITIMAX 400", "municipio": "SAO PAULO"})

    assert resultado.count("[CONTEXTO CTI]") == 1
    assert "Tipo da oportunidade: Cotação / tomada de preços" in resultado
    assert "Observação comercial" in resultado
    assert "equipamentos: CITIMAX 400" in resultado
    assert "equipamentos: ANTIGO" not in resultado
