from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from services.historical_quality_audit import audit_dataset, audit_record


def rec(**kwargs):
    defaults = dict(
        aba_origem="BACKLOG",
        linha_origem=6,
        data_normalizada=date(2024, 1, 10),
        canal_venda="DIRETA",
        quantidade=1,
        valor_unitario=Decimal("100"),
        valor_total=Decimal("100"),
        status_normalizado="GANHO",
        flags_validacao=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def norm(**kwargs):
    defaults = dict(
        canal_venda="DIRETA",
        quantidade_normalizada=Decimal("1"),
        valor_unitario_normalizado=Decimal("100"),
        valor_total_normalizado=Decimal("100"),
        status_normalizado="GANHO",
        flags_validacao=(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def reconciliation(status="RECONCILIADO", metodo="EXATO_NORMALIZADO", confianca=1.0, flags=()):
    return SimpleNamespace(status=status, metodo=metodo, confianca=confianca, flags=flags)


def test_audit_record_detecta_divergencia_aritmetica():
    findings = audit_record(rec(), norm(valor_total_normalizado=Decimal("90")))
    assert any(f.codigo == "DIVERGENCIA_ARITMETICA" and f.severidade == "ERRO" for f in findings)


def test_audit_record_preserva_ambiguidade_para_revisao_humana():
    findings = audit_record(
        rec(),
        norm(),
        {"cliente": reconciliation("AMBIGUO", "FUZZY_REVISAO_HUMANA", 0.89)},
    )
    assert any(f.codigo == "RECONCILIACAO_AMBIGUA" and f.entidade == "cliente" for f in findings)


def test_nao_aplicavel_implementadora_direta_nao_vira_pendencia():
    findings = audit_record(
        rec(),
        norm(),
        {"implementadora": reconciliation("NAO_ENCONTRADO", "NAO_APLICAVEL_CANAL_DIRETO", 1.0, ("NAO_APLICAVEL",))},
    )
    assert not any(f.entidade == "implementadora" for f in findings)


def test_relatorio_agrega_aba_ano_canal_status_valores_e_reconciliacao():
    records = [
        rec(aba_origem="BACKLOG", data_normalizada=date(2023, 2, 1), quantidade=2, valor_total=Decimal("200")),
        rec(aba_origem="INTERMEDIAÇÃO - OEM", linha_origem=7, data_normalizada=date(2024, 3, 1), canal_venda="INDIRETA_OEM", quantidade=3, valor_total=Decimal("450")),
    ]
    normalized = [
        norm(quantidade_normalizada=Decimal("2"), valor_total_normalizado=Decimal("200"), status_normalizado="GANHO"),
        norm(canal_venda="INDIRETA_OEM", quantidade_normalizada=Decimal("3"), valor_unitario_normalizado=Decimal("150"), valor_total_normalizado=Decimal("450"), status_normalizado="PERDIDO"),
    ]
    reconciliations = [
        {"cliente": reconciliation(), "representante": reconciliation(), "equipamento": reconciliation()},
        {"cliente": reconciliation("AMBIGUO"), "representante": reconciliation(), "equipamento": reconciliation("NAO_ENCONTRADO"), "implementadora": reconciliation()},
    ]
    report = audit_dataset(records, normalized, reconciliations)
    assert report.total_registros == 2
    assert report.por_aba == {"BACKLOG": 1, "INTERMEDIAÇÃO - OEM": 1}
    assert report.por_ano == {"2023": 1, "2024": 1}
    assert report.por_canal == {"DIRETA": 1, "INDIRETA_OEM": 1}
    assert report.por_status == {"GANHO": 1, "PERDIDO": 1}
    assert report.unidades == "5"
    assert report.valor_total_nominal == "650.00"
    assert report.reconciliacao["cliente"]["AMBIGUO"] == 1
    assert report.reconciliacao["equipamento"]["NAO_ENCONTRADO"] == 1
    assert report.impacto_analitico_esperado["analise_perdas"] is True
    assert report.impacto_analitico_esperado["canal_direto_vs_oem"] is True
    assert report.impacto_analitico_esperado["cruzamento_anfir_crm"] is False


def test_erros_sao_rejeitados_para_homologacao_sem_apagar_registro():
    report = audit_dataset(
        [rec(flags_validacao=["DATA_INVALIDA"])],
        [norm()],
        [{}],
    )
    assert report.rejeitados == 1
    assert report.registros_com_erro == 1
    assert report.registros_sem_bloqueio == 0
    assert report.total_registros == 1


def test_aviso_nao_rejeita_registro():
    report = audit_dataset(
        [rec(flags_validacao=["PROBABILIDADE_ZERO_NAO_CONFIAVEL"])],
        [norm()],
        [{}],
    )
    assert report.rejeitados == 0
    assert report.registros_com_aviso == 1
    assert report.registros_sem_bloqueio == 1


def test_tamanhos_inconsistentes_sao_bloqueados():
    try:
        audit_dataset([rec()], [], [])
    except ValueError as exc:
        assert "mesmo tamanho" in str(exc)
    else:
        raise AssertionError("ValueError esperado")
