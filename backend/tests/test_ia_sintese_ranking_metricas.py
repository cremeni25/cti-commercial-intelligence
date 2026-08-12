from services import ia_comercial_agente_crm as crm
import services.ia_comercial_sintese_crm  # noqa: F401  # aplica fachada/guardrails


def test_sintese_universal_nomeia_metrica_e_nao_extrapola_ranking_nacional():
    instrucao = crm._instrucao_sintese_final_universal({"universo_cti", "web"})
    texto = instrucao.casefold()

    assert "quantidade/frequência de registros" in texto
    assert "não o chame de maior do brasil" in texto
    assert "mais frequentes/maior número de registros no cti" in texto
    assert "faturamento" in texto
    assert "market share" in texto


def test_sintese_universal_separa_ranking_web_com_entidades_diferentes():
    instrucao = crm._instrucao_sintese_final_universal({"universo_cti", "web"})
    texto = instrucao.casefold()

    assert "mesmas entidades retornadas pelo cti" in texto
    assert "ranking externo" in texto
    assert "não misture as listas" in texto
    assert "métrica/fonte" in texto


def test_sintese_universal_exige_limitacao_sem_metrica_externa_comparavel():
    instrucao = crm._instrucao_sintese_final_universal({"universo_cti", "web"})
    texto = instrucao.casefold()

    assert "fonte externa comparável" in texto
    assert "declare essa limitação explicitamente" in texto
    assert "liderança" in texto
    assert "qualifique como inferência ou omita" in texto


def test_instrucoes_agente_web_buscam_metrica_objetiva_para_ranking_nacional():
    texto = crm._INSTRUCOES_UNIVERSAIS.casefold()

    assert "rankings, porte e comparação externa" in texto
    assert "métrica objetiva comparável" in texto
    assert "não force um ranking nacional" in texto
    assert "priorize validar as entidades retornadas pelo cti" in texto
