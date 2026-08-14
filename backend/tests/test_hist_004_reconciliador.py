from types import SimpleNamespace

from services.historical_reconciliation import (
    Candidate,
    reconcile_cliente,
    reconcile_equipamento,
    reconcile_implementadora,
    reconcile_record,
    reconcile_representante,
    valid_cnpj,
)


def test_cnpj_valido_e_match_deterministico():
    assert valid_cnpj("11.222.333/0001-81")
    result = reconcile_cliente(
        "CLIENTE ANTIGO",
        "CLIENTE ANTIGO",
        [Candidate("c1", "CLIENTE CANONICO", "11.222.333/0001-81")],
        "11.222.333/0001-81",
    )
    assert result.status == "RECONCILIADO"
    assert result.metodo == "CNPJ_EXATO"
    assert result.candidato_id == "c1"


def test_cliente_exato_normalizado_e_fuzzy_ambiguo():
    exact = reconcile_cliente(
        "Transp. Alpha",
        "TRANSPORTADORA ALPHA",
        [Candidate("1", "TRANSPORTADORA ALPHA")],
    )
    assert exact.status == "RECONCILIADO"
    assert exact.metodo == "EXATO_NORMALIZADO"

    ambiguous = reconcile_cliente(
        "ALFA TRANSPORT",
        "ALFA TRANSPORT",
        [Candidate("1", "ALFA TRANSPORTES"), Candidate("2", "ALFA TRANSPORTADORA")],
    )
    assert ambiguous.status == "AMBIGUO"
    assert ambiguous.metodo == "FUZZY_REVISAO_HUMANA"
    assert ambiguous.candidato_id is None


def test_representante_carla_preserva_origem_mas_reconcilia_monica():
    result = reconcile_representante(
        "CARLA - VIENA SP",
        "MÔNICA - VIENA SP",
        [Candidate("m1", "MÔNICA - VIENA SP")],
    )
    assert result.status == "RECONCILIADO"
    assert result.valor_original == "CARLA - VIENA SP"
    assert result.candidato_nome == "MÔNICA - VIENA SP"


def test_representante_viena_sp_nao_e_atribuido_arbitrariamente():
    result = reconcile_representante(
        "VIENA SP",
        "VIENA SP",
        [Candidate("a1", "ANDERSON - VIENA SP")],
    )
    assert result.status == "AMBIGUO"
    assert "REPRESENTANTE_NAO_INDIVIDUALIZADO" in result.flags


def test_equipamento_historico_nao_catalogado_nao_e_descartado():
    result = reconcile_equipamento(
        "CITIMAX 700",
        "CITIMAX 700",
        [Candidate("e1", "CITIMAX 500", codigo="CM500")],
    )
    assert result.status == "NAO_ENCONTRADO"
    assert result.valor_original == "CITIMAX 700"


def test_implementadora_composta_permanece_ambigua():
    result = reconcile_implementadora(
        "RANDON/MULTIEIXO",
        None,
        [Candidate("r1", "RANDON"), Candidate("m1", "MULTIEIXO")],
    )
    assert result.status == "AMBIGUO"
    assert result.candidato_id is None
    assert "IMPLEMENTADORA_COMPOSTA_AMBIGUA" in result.flags


def test_reconcile_record_e_read_only_e_canal_direto_nao_aplica_implementadora():
    record = SimpleNamespace(
        cliente_original="CLIENTE A",
        representante_original="CARLA - VIENA SP",
        equipamento_original="X4-7500",
        implementadora_original=None,
        cnpj_original=None,
    )
    normalized = SimpleNamespace(
        cliente_normalizado="CLIENTE A",
        representante_normalizado="MÔNICA - VIENA SP",
        equipamento_normalizado="X4 7500",
        implementadora_normalizada=None,
        canal_venda="DIRETA",
    )
    catalogs = {
        "clientes": [Candidate("c1", "CLIENTE A")],
        "representantes": [Candidate("m1", "MÔNICA - VIENA SP")],
        "equipamentos": [Candidate("e1", "X4 7500")],
        "implementadoras": [],
    }
    result = reconcile_record(record, normalized, catalogs)
    assert result["cliente"].status == "RECONCILIADO"
    assert result["representante"].candidato_id == "m1"
    assert result["equipamento"].candidato_id == "e1"
    assert "NAO_APLICAVEL" in result["implementadora"].flags
    assert record.representante_original == "CARLA - VIENA SP"
    assert normalized.representante_normalizado == "MÔNICA - VIENA SP"
