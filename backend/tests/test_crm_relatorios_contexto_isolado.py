from services.ia_comercial_artefatos_patch import _relatorio_crm_isolado


def test_reconhece_relatorios_tematicos_do_crm():
    assert _relatorio_crm_isolado("RELATÓRIO CRM — PIPELINE EXECUTIVO. Gere PDF.")
    assert _relatorio_crm_isolado("RELATÓRIO CRM — ATIVIDADES COMERCIAIS. Gere PDF.")
    assert _relatorio_crm_isolado("RELATÓRIO CRM — FORECAST COMERCIAL. Gere PDF.")
    assert _relatorio_crm_isolado("RELATÓRIO CRM — CARTEIRA DE CLIENTES. Gere PDF.")


def test_nao_isola_pergunta_comum_da_ia():
    assert not _relatorio_crm_isolado("Qual é a próxima ação deste cliente?")
    assert not _relatorio_crm_isolado("Gere um gráfico da resposta acima")
