from services import ia_comercial_agente as agente


def test_semantica_oportunidade_ganha_bloqueia_avanco_e_sinaliza_qualidade():
    registro = {
        "id": "opp-ganha",
        "titulo": "Proposta Comercial",
        "status": "GANHO",
        "probabilidade": 50,
        "data_fechamento_real": None,
        "valor_estimado": 105000,
    }

    resultado = agente._semantica_oportunidade(registro)
    semantica = resultado["semantica_pipeline"]

    assert semantica["estado_pipeline"] == "encerrada_ganha"
    assert semantica["pode_avancar_pipeline"] is False
    assert "status GANHO com probabilidade inferior a 100%" in semantica["inconsistencias_qualidade"]
    assert "status encerrado sem data_fechamento_real" in semantica["inconsistencias_qualidade"]


def test_semantica_oportunidade_aberta_permite_avanco():
    registro = {
        "id": "opp-aberta",
        "titulo": "Nova oportunidade",
        "status": "ABERTO",
        "probabilidade": 40,
        "data_fechamento_real": None,
    }

    resultado = agente._semantica_oportunidade(registro)
    semantica = resultado["semantica_pipeline"]

    assert semantica["estado_pipeline"] == "aberta"
    assert semantica["pode_avancar_pipeline"] is True
    assert semantica["inconsistencias_qualidade"] == []


def test_instrucao_sintese_proibe_avancar_ganho():
    instrucao = agente._instrucao_sintese_final({"clientes_oportunidades", "cti_atual"})

    assert "nunca recomende avançar uma oportunidade GANHO" in instrucao
    assert "pode_avancar_pipeline=true" in instrucao
    assert "qualidade de dado" in instrucao
