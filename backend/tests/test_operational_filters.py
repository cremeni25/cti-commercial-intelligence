from datetime import date

from services.operational_filters import filtrar_registros, resolver_periodo


REGISTROS = [
    {"origem_base": "BRASIL", "estado": "RJ", "ddd": "021", "data_venda": "2026-01-10", "cliente": "RJ", "chassi": "RJ-1"},
    {"origem_base": "VIENA_SP", "autorizado": "VIENA", "estado": "SP", "ddd": "011", "data_venda": "2026-02-10", "cliente": "VIENA 11", "chassi": "SP-1"},
    {"origem_base": "VIENA_SP", "autorizado": "VIENA", "estado": "SP", "ddd": "013", "data_venda": "2025-02-10", "cliente": "VIENA 13", "chassi": "SP-2"},
    {"origem_base": "BRASIL", "estado": "SP", "ddd": "011", "data_venda": "2026-02-10", "cliente": "OUTRO SP", "chassi": "SP-3"},
    # Mesmo evento em duas origens: deve contar apenas uma vez no Brasil e em SP.
    {"origem_base": "BRASIL", "estado": "SP", "ddd": "011", "data_venda": "2026-03-10", "cliente": "DUP BR", "chassi": "DUP-1"},
    {"origem_base": "VIENA_SP", "autorizado": "VIENA", "estado": "SP", "ddd": "011", "data_venda": "2026-03-10", "cliente": "DUP VIENA", "chassi": "DUP-1"},
]


def test_contexto_brasil_retorna_visao_total_deduplicada():
    resultado = filtrar_registros(REGISTROS, contexto="brasil")
    assert len(resultado) == 5
    assert {item["chassi"] for item in resultado} == {"RJ-1", "SP-1", "SP-2", "SP-3", "DUP-1"}


def test_contexto_viena_retorna_apenas_registros_do_autorizado():
    resultado = filtrar_registros(REGISTROS, contexto="viena-sp")
    assert {item["cliente"] for item in resultado} == {"VIENA 11", "VIENA 13", "DUP VIENA"}
    assert all(item["origem_base"] == "VIENA_SP" for item in resultado)


def test_contexto_uf_consolida_todas_as_origens_da_unidade():
    resultado = filtrar_registros(REGISTROS, contexto="uf-sp")
    assert len(resultado) == 4
    assert {item["chassi"] for item in resultado} == {"SP-1", "SP-2", "SP-3", "DUP-1"}


def test_contexto_uf_rj_retorna_apenas_rj():
    resultado = filtrar_registros(REGISTROS, contexto="uf-rj")
    assert [item["cliente"] for item in resultado] == ["RJ"]


def test_contexto_ddd_aplica_territorio_e_autorizado_viena():
    resultado = filtrar_registros(REGISTROS, contexto="ddd-011")
    assert {item["cliente"] for item in resultado} == {"VIENA 11", "DUP VIENA"}


def test_intervalo_temporal_remove_registros_sem_correspondencia():
    resultado = filtrar_registros(
        REGISTROS,
        contexto="viena-sp",
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )
    assert {item["cliente"] for item in resultado} == {"VIENA 11", "DUP VIENA"}


def test_todo_historico_nao_impoe_datas():
    assert resolver_periodo("TODO_HISTORICO") == (None, None)