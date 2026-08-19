from core.data_semantics import contrato_dashboard, contrato_fonte, validar_correlacao


def test_anfir_e_fato_realizado_e_nao_compoe_funil():
    contrato = contrato_fonte("ANFIR")
    assert contrato["natureza"] == "FATO_MERCADO_REALIZADO"
    assert contrato["pode_compor_funil"] is False
    assert contrato["pode_criar_oportunidade"] is False


def test_crm_compoe_funil_sem_confundir_com_anfir():
    crm = contrato_fonte("CRM")
    funil = contrato_fonte("FUNIL")
    assert crm["pode_compor_funil"] is True
    assert funil["natureza"] == "CICLO_DE_OPORTUNIDADE"


def test_dashboard_executivo_separa_realizado_e_em_curso():
    contrato = contrato_dashboard("DASHBOARD_EXECUTIVO")
    assert contrato["realizado"] == "ANFIR"
    assert contrato["em_curso"] == "FUNIL"
    assert contrato["regra"] == "CAMADAS_SEPARADAS_SEM_FUSAO"


def test_segundo_dashboard_e_somente_mercado_realizado():
    contrato = contrato_dashboard("INTELIGENCIA_MERCADO")
    assert contrato["fonte"] == "ANFIR"
    assert contrato["metricas_funil_permitidas"] is False


def test_anfir_pode_correlacionar_com_funil_mas_nunca_fundir():
    regra = validar_correlacao("ANFIR", "FUNIL")
    assert regra["permitido"] is True
    assert regra["modo"] == "CORRELACAO_ANALITICA"
    assert regra["fusao_registros"] is False
    assert regra["promocao_automatica"] is False
