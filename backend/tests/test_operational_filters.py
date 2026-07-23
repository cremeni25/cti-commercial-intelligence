from datetime import date

from services.operational_filters import filtrar_registros, resolver_periodo


REGISTROS = [
    {"origem_base": "BRASIL", "estado": "RJ", "ddd": "021", "data_venda": "2026-01-10", "cliente": "RJ"},
    {"origem_base": "VIENA_SP", "autorizado": "VIENA", "estado": "SP", "ddd": "011", "data_venda": "2026-02-10", "cliente": "VIENA 11"},
    {"origem_base": "VIENA_SP", "autorizado": "VIENA", "estado": "SP", "ddd": "013", "data_venda": "2025-02-10", "cliente": "VIENA 13"},
    {"origem_base": "BRASIL", "estado": "SP", "ddd": "011", "data_venda": "2026-02-10", "cliente": "OUTRO SP"},
]


def test_contexto_brasil_retorna_base_completa():
    assert len(filtrar_registros(REGISTROS, contexto="brasil")) == 4


def test_contexto_viena_retorna_apenas_registros_do_autorizado():
    resultado = filtrar_registros(REGISTROS, contexto="viena-sp")
    assert {item["cliente"] for item in resultado} == {"VIENA 11", "VIENA 13"}


def test_contexto_uf_aplica_unidade_federativa():
    resultado = filtrar_registros(REGISTROS, contexto="uf-rj")
    assert [item["cliente"] for item in resultado] == ["RJ"]


def test_contexto_ddd_aplica_territorio_e_autorizado_viena():
    resultado = filtrar_registros(REGISTROS, contexto="ddd-011")
    assert [item["cliente"] for item in resultado] == ["VIENA 11"]


def test_intervalo_temporal_remove_registros_sem_correspondencia():
    resultado = filtrar_registros(
        REGISTROS,
        contexto="viena-sp",
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )
    assert [item["cliente"] for item in resultado] == ["VIENA 11"]


def test_todo_historico_nao_impoe_datas():
    assert resolver_periodo("TODO_HISTORICO") == (None, None)
