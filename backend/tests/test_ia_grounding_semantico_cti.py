from services import ia_comercial_agente_crm as crm


def test_pergunta_real_exige_cti_e_web():
    pergunta = "entre os dados contidos no cti e através de pesquisa na web, relacione as 05 maiores implementadoras do Brasil"

    requeridas = crm._fontes_requeridas_ia003(pergunta)

    assert "implementadoras_cti" in requeridas
    assert "web" in requeridas
    assert requeridas != {"web"}


def test_pesquisa_na_web_e_reconhecida_como_web_explicita():
    pergunta = "através de pesquisa na web, verifique as maiores implementadoras"

    assert crm._necessita_web_autonoma(pergunta) is True


def test_referencia_generica_ao_cti_e_reconhecida_como_cruzamento():
    pergunta = "entre os dados contidos no CTI, quais implementadoras mais aparecem?"

    assert crm._pede_cruzamento_cti_explicito(pergunta) is True


def test_implementadora_sem_web_continua_ancorada_no_cti():
    pergunta = "quais são as maiores implementadoras do Brasil?"

    requeridas = crm._fontes_requeridas_ia003(pergunta)

    assert requeridas == {"implementadoras_cti"}


def test_instrucao_de_evidencia_separa_implementadora_de_fabricante():
    instrucao = crm._instrucao_evidencias_faltantes_crm({"implementadoras_cti"})

    assert "consultar_territorio_cti" in instrucao
    assert "ranking_implementadoras" in instrucao
    assert "ranking_fabricantes_equipamento" in instrucao
    assert "não use" in instrucao


def test_sintese_cti_first_nao_permite_substituicao_por_fabricantes():
    instrucao = crm._instrucao_sintese_final_crm({"implementadoras_cti", "web"})

    assert "ranking_implementadoras" in instrucao
    assert "Não substitua implementadoras por fabricantes de equipamento" in instrucao
    assert "frequência/volume de registros históricos" in instrucao
    assert "mesmas implementadoras" in instrucao


def test_grounding_semantico_faz_parte_do_prompt_final():
    crm._aplicar_patch()

    assert "GROUNDING SEMÂNTICO CTI" in crm.base.INSTRUCOES_AGENTE
    assert "linguagem comercial natural" in crm.base.INSTRUCOES_AGENTE
    assert "IMPLEMENTADORA" in crm.base.INSTRUCOES_AGENTE
    assert "FABRICANTE DE EQUIPAMENTO" in crm.base.INSTRUCOES_AGENTE
