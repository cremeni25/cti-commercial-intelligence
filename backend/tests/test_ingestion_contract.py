from core.ingestion_contract import (
    contrato_backoffice_fontes,
    contrato_upload_operacional,
    validar_contrato,
)


def test_duas_entradas_compartilham_mesmo_nucleo_e_pipeline():
    operacional = contrato_upload_operacional("dados.xlsx", "viena_sp")
    master = contrato_backoffice_fontes("dados.xlsx", "cti_web")

    assert validar_contrato(operacional)
    assert validar_contrato(master)
    assert operacional["nucleo"] == master["nucleo"] == "CTI_INGESTAO_CANONICA"
    assert operacional["pipeline_canonico"] == master["pipeline_canonico"]


def test_upload_operacional_e_backoffice_preservam_responsabilidades_distintas():
    operacional = contrato_upload_operacional("dados.xlsx")
    master = contrato_backoffice_fontes("dados.xlsx")

    assert operacional["entrada"] == "UPLOAD_OPERACIONAL"
    assert operacional["persistencia_operacional_automatica"] is True
    assert operacional["governanca_master"] is False

    assert master["entrada"] == "BACKOFFICE_FONTES"
    assert master["persistencia_operacional_automatica"] is False
    assert master["governanca_master"] is True
