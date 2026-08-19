import pytest

from core.ingestion_promotion import suporte_promocao, validar_lote


def test_somente_anfir_e_cliente_possuem_adaptador_operacional_seguro():
    assert suporte_promocao("CTI_ANFIR", "ANFIR")["suportado"] is True
    assert suporte_promocao("CRM_COMERCIAL", "CLIENTE")["suportado"] is True
    assert suporte_promocao("CRM_COMERCIAL", "OPORTUNIDADE")["suportado"] is False
    assert suporte_promocao("CRM_COMERCIAL", "VENDA")["suportado"] is False
    assert suporte_promocao("CTI_TERRITORIAL", "TERRITORIO")["suportado"] is False
    assert suporte_promocao("CTI_FINANCEIRO", "FINANCEIRO")["suportado"] is False


def test_lote_so_promove_depois_de_pronto_promocao():
    with pytest.raises(ValueError):
        validar_lote({"status": "PREPARADA", "dominio_alvo": "CTI_ANFIR"}, [{"id": "1", "status_item": "PRONTO_PROMOCAO", "entidade_sugerida": "ANFIR"}])


def test_lote_anfir_pronto_e_aprovado():
    resultado = validar_lote(
        {"status": "PRONTO_PROMOCAO", "dominio_alvo": "CTI_ANFIR"},
        [{"id": "1", "status_item": "PRONTO_PROMOCAO", "entidade_sugerida": "ANFIR"}],
    )
    assert resultado["aprovado"] is True
    assert resultado["bloqueios"] == []


def test_lote_com_entidade_sem_adaptador_e_bloqueado_antes_da_escrita():
    resultado = validar_lote(
        {"status": "PRONTO_PROMOCAO", "dominio_alvo": "CRM_COMERCIAL"},
        [{"id": "1", "status_item": "PRONTO_PROMOCAO", "entidade_sugerida": "OPORTUNIDADE"}],
    )
    assert resultado["aprovado"] is False
    assert resultado["bloqueios"]
