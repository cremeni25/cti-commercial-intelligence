from services import ia_comercial_agente_crm as crm
import services.ia_comercial_sintese_crm  # noqa: F401  # aplica guardrails canônicos


def test_sintese_universal_nomeia_metrica_e_nao_extrapola_ranking_nacional():
    instrucao = crm._instrucao_sintese_final_universal({"universo_cti", "web"})
    texto = instrucao.casefold()

    assert "ranking e métrica" in texto
    assert "frequência de registros cti" in texto
    assert "não representa automaticamente porte" in texto
    assert "faturamento" in texto
    assert "market share" in texto
    assert "liderança nacional" in texto


def test_sintese_universal_separa_ranking_web_com_entidades_diferentes():
    instrucao = crm._instrucao_sintese_final_universal({"universo_cti", "web"})
    texto = instrucao.casefold()

    assert "valide as mesmas entidades" in texto
    assert "rankings externos separados" in texto
    assert "métrica não for comparável" in texto


def test_sintese_universal_exige_limitacao_sem_metrica_externa_comparavel():
    instrucao = crm._instrucao_sintese_final_universal({"universo_cti", "web"})
    texto = instrucao.casefold()

    assert "evidência externa comparável" in texto
    assert "declare a limitação" in texto
    assert "ranking nacional" in texto


def test_instrucoes_agente_web_buscam_metrica_objetiva_para_ranking_nacional():
    texto = crm._INSTRUCOES_UNIVERSAIS.casefold()

    assert "rankings, porte e comparação externa" in texto
    assert "evidência externa objetiva e comparável" in texto
    assert "métrica comparável verificável" in texto
    assert "entidades cti" in texto
