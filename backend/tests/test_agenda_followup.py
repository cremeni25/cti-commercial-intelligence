from datetime import date

from routers.negociacoes_router import _situacao_atividade


def test_classifica_atividade_atrasada():
    atividade = {"status": "PENDENTE", "data": "2026-07-22"}
    assert _situacao_atividade(atividade, date(2026, 7, 23)) == "ATRASADA"


def test_classifica_atividade_do_dia():
    atividade = {"status": "PENDENTE", "data": "2026-07-23"}
    assert _situacao_atividade(atividade, date(2026, 7, 23)) == "HOJE"


def test_classifica_atividade_futura():
    atividade = {"status": "PENDENTE", "data": "2026-07-24"}
    assert _situacao_atividade(atividade, date(2026, 7, 23)) == "FUTURA"


def test_status_concluido_prevalece_sobre_data():
    atividade = {"status": "CONCLUIDA", "data": "2026-07-20"}
    assert _situacao_atividade(atividade, date(2026, 7, 23)) == "CONCLUIDA"


def test_atividade_sem_data_fica_identificada():
    atividade = {"status": "PENDENTE"}
    assert _situacao_atividade(atividade, date(2026, 7, 23)) == "SEM_DATA"
