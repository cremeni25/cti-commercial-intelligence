from services.commercial_truth import _desfecho, _ordem_temporal_valida, _temporalidade_funil_historico


def test_cadeia_crm_funil_anfir_carrier_confirma_sucesso():
    eventos = [
        {"fonte": "CRM", "data_evento": "2026-01-10", "estado_comercial": "CONCLUIDA"},
        {"fonte": "FUNIL", "data_evento": "2026-02-15", "estado_comercial": "BACKLOG", "temporalidade": "EM_CURSO_BACKLOG"},
        {"fonte": "ANFIR", "data_evento": "2026-03-01", "estado_comercial": "CARRIER"},
    ]
    assert _desfecho(eventos) == "SUCESSO_COMERCIAL_CONFIRMADO"
    assert _ordem_temporal_valida(eventos) is True


def test_mencao_concorrente_anfir_nao_vira_sucesso():
    eventos = [
        {"fonte": "CRM", "data_evento": "2026-01-10", "estado_comercial": "CONCLUIDA"},
        {"fonte": "FUNIL", "data_evento": "2026-02-15", "estado_comercial": "PERDIDO", "temporalidade": "PASSADO_CONFIRMADO"},
        {"fonte": "ANFIR", "data_evento": "2026-03-01", "estado_comercial": "TK"},
    ]
    assert _desfecho(eventos) == "RESULTADO_CONCORRENTE_CONFIRMADO"


def test_funil_aberto_permanece_backlog_sem_anfir():
    eventos = [
        {"fonte": "CRM", "data_evento": "2026-05-10", "estado_comercial": "CONCLUIDA"},
        {"fonte": "FUNIL", "data_evento": "2026-06-01", "estado_comercial": "ABERTA", "temporalidade": "EM_CURSO_BACKLOG"},
    ]
    assert _desfecho(eventos) == "EM_CURSO_BACKLOG"


def test_ordem_temporal_invertida_nao_e_confirmada():
    eventos = [
        {"fonte": "ANFIR", "data_evento": "2026-01-01", "estado_comercial": "CARRIER"},
        {"fonte": "FUNIL", "data_evento": "2026-02-01", "estado_comercial": "GANHO", "temporalidade": "PASSADO_CONFIRMADO"},
        {"fonte": "CRM", "data_evento": "2026-03-01", "estado_comercial": "CONCLUIDA"},
    ]
    assert _ordem_temporal_valida(eventos) is False


def test_funil_historico_temporalidades_sao_explicitas():
    assert _temporalidade_funil_historico("Venda concluída") == "PASSADO_CONFIRMADO"
    assert _temporalidade_funil_historico("Backlog") == "EM_CURSO_BACKLOG"
    assert _temporalidade_funil_historico("Prospecção") == "PROSPECCAO"
    assert _temporalidade_funil_historico("A revisar") == "HISTORICO_INDETERMINADO"
