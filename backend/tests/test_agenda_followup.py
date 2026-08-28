from datetime import date

from routers.crm_scope_atividades_router import _resumo_agenda, _situacao_calendario
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


def test_calendario_independe_de_atividade_concluida():
    atividade = {"status": "CONCLUIDA", "situacao": "CONCLUIDA", "data": "2026-08-28"}
    assert _situacao_calendario(atividade, date(2026, 8, 28)) == "HOJE"


def test_resumo_permite_mesma_atividade_em_hoje_e_concluidas():
    itens = [
        {"status": "CONCLUIDA", "situacao": "CONCLUIDA", "situacao_calendario": "ATRASADA"},
        {"status": "CONCLUIDA", "situacao": "CONCLUIDA", "situacao_calendario": "HOJE"},
        {"status": "PENDENTE", "situacao": "FUTURA", "situacao_calendario": "FUTURA"},
    ]
    resumo = _resumo_agenda(itens)
    assert resumo == {
        "total": 3,
        "atrasadas": 1,
        "hoje": 1,
        "futuras": 1,
        "sem_data": 0,
        "concluidas": 2,
    }
