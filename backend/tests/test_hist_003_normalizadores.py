from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from services.historical_normalization import (
    normalize_data,
    normalize_equipamento,
    normalize_implementadora,
    normalize_previsao,
    normalize_probabilidade,
    normalize_record,
    normalize_representante,
    normalize_status,
)


def test_representante_preserva_sucessao_carla_para_monica():
    normalized, flags = normalize_representante("CARLA - VIENA SP")
    assert normalized == "MÔNICA - VIENA SP"
    assert "REPRESENTANTE_SUBSTITUIDO_CARLA_POR_MONICA" in flags


def test_previsao_mes_e_data_sem_inventar_dia():
    mes = normalize_previsao("setembo", 2025)
    assert mes == {
        "previsao_mes": 9,
        "previsao_ano": 2025,
        "previsao_data": None,
        "precisao_previsao": "MES",
    }
    data = normalize_previsao("15/08/2025", 2025)
    assert data["previsao_data"] == date(2025, 8, 15)
    assert data["precisao_previsao"] == "DATA"


def test_probabilidade_zero_oportunidade_eh_preservada_mas_nao_confiavel():
    value, confidence, flags = normalize_probabilidade(0, "OPORTUNIDADE")
    assert value == Decimal("0")
    assert confidence == Decimal("0")
    assert "PROBABILIDADE_ZERO_NAO_CONFIAVEL" in flags


def test_status_separa_estado_e_motivo():
    status, motivo, flags = normalize_status("Cancelado por preço", "OPORTUNIDADE")
    assert status == "PERDIDO"
    assert motivo == "PRECO"
    assert flags == []

    status, motivo, _ = normalize_status("aguardando pagamento banco", "BACKLOG")
    assert status == "FINANCEIRO_PENDENTE"
    assert motivo is None


def test_implementadora_alias_e_composta_ambigua():
    normalized, flags = normalize_implementadora("Bortoloto Ibiporã")
    assert normalized == "IBIPORÃ"
    assert "IMPLEMENTADORA_ALIAS_BORTOLOTO_IBIPORA" in flags

    normalized, flags = normalize_implementadora("RANDON/MULTIEIXO")
    assert normalized is None
    assert "IMPLEMENTADORA_COMPOSTA_AMBIGUA" in flags


def test_equipamento_preserva_configuracoes_nao_catalogadas():
    normalized, flags = normalize_equipamento("Supra 1150MT 24V")
    assert normalized == "SUPRA 1150MT 24V"
    assert "EQUIPAMENTO_NAO_CATALOGADO" in flags


def test_normalize_record_nao_promove_nem_inventa_relacionamentos():
    record = SimpleNamespace(
        aba_origem="INTERMEDIAÇÃO - OEM",
        cliente_original="  Cliente Teste Ltda  ",
        representante_original="CARLA - VIENA SP",
        equipamento_original="Vector HE19",
        quantidade=2,
        valor_unitario=Decimal("100000"),
        valor_total=Decimal("200000"),
        data_original="01/08/2025",
        data_normalizada=date(2025, 8, 1),
        previsao_original="setembro",
        probabilidade_original=None,
        observacao_original="em negociação",
        canal_venda="INDIRETA_OEM",
        implementadora_original="PAVAN",
    )
    result = normalize_record(record)
    assert result.representante_normalizado == "MÔNICA - VIENA SP"
    assert result.equipamento_normalizado == "VECTOR HE19"
    assert result.canal_venda == "INDIRETA_OEM"
    assert result.implementadora_normalizada == "PAVAN"
    assert result.previsao_mes == 9
    assert result.previsao_data is None
    assert result.valor_total_normalizado == Decimal("200000")
    assert "REPRESENTANTE_SUBSTITUIDO_CARLA_POR_MONICA" in result.flags_validacao


def test_normalize_data_formatos_controlados():
    assert normalize_data("14/08/2026") == date(2026, 8, 14)
    assert normalize_data("2026-08-14") == date(2026, 8, 14)
    assert normalize_data("agosto") is None
