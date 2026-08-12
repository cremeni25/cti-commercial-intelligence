from services import ia_comercial_agente_crm as crm


def test_pergunta_real_exige_catalogo_consulta_universal_e_web():
    pergunta = "entre os dados contidos no cti e através de pesquisa na web, relacione as 05 maiores implementadoras do Brasil"

    requeridas = crm._fontes_requeridas_universais(pergunta)

    assert requeridas == {"catalogo_cti", "universo_cti", "web"}


def test_qualquer_pergunta_cti_nao_depende_de_palavra_chave_de_dominio():
    perguntas = [
        "quem aparece mais vezes?",
        "onde temos maior concentração?",
        "o que merece atenção hoje?",
        "qual cliente tem mais histórico?",
        "quais são as maiores implementadoras?",
    ]

    for pergunta in perguntas:
        requeridas = crm._fontes_requeridas_universais(pergunta)
        assert "catalogo_cti" in requeridas
        assert "universo_cti" in requeridas


def test_catalogo_so_nao_satisfaz_evidencia_factual():
    rastreio = [
        {"tipo": "CTI", "ferramenta": "catalogar_universo_cti", "argumentos": {}, "resumo": {"erro": None}},
    ]

    presentes = crm._evidencias_presentes_universais(rastreio, [])

    assert "catalogo_cti" in presentes
    assert "universo_cti" not in presentes


def test_consulta_universal_satisfaz_evidencia_factual():
    rastreio = [
        {"tipo": "CTI", "ferramenta": "consultar_universo_cti", "argumentos": {"fonte": "historico_anfir"}, "resumo": {"erro": None}},
    ]

    presentes = crm._evidencias_presentes_universais(rastreio, [])

    assert "universo_cti" in presentes


def test_prompt_final_proibe_dicionario_de_palavras_chave_e_sql_livre():
    crm._aplicar_patch()
    instrucoes = crm.base.INSTRUCOES_AGENTE.casefold()

    assert "linguagem natural livre" in instrucoes
    assert "nunca exija palavras-chave" in instrucoes
    assert "não existe uma ferramenta diferente para cada palavra ou entidade" in instrucoes
    assert "não é sql livre" in instrucoes
    assert "implementadora e fabricante de equipamento são conceitos distintos" in instrucoes
    assert "ontologia comercial cti" in instrucoes


def test_ferramentas_universais_nao_expoem_dominio_especifico():
    token = crm._EXECUCAO_WEB_PURA.set(False)
    try:
        ferramentas = crm._ferramentas_universais()
    finally:
        crm._EXECUCAO_WEB_PURA.reset(token)

    nomes = {item.get("name") for item in ferramentas if item.get("type") == "function"}
    assert nomes == {"catalogar_universo_cti", "consultar_universo_cti"}
    assert not any("implementadora" in str(nome) for nome in nomes)
    assert not any("cliente" in str(nome) for nome in nomes)
    assert not any("pedido" in str(nome) for nome in nomes)
