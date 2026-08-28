import pytest
from fastapi import HTTPException

import routers.crm_scope_documents_router as modulo


def test_assinatura_temporaria_valida(monkeypatch):
    monkeypatch.setenv("CTI_DOCUMENT_PREVIEW_SECRET", "segredo-de-teste-cti")
    monkeypatch.setattr(modulo.time, "time", lambda: 1_000)
    expira_em = 1_200
    assinatura = modulo._assinatura("proposta-1", expira_em)
    modulo._validar_assinatura("proposta-1", expira_em, assinatura)


def test_assinatura_nao_pode_ser_reutilizada_em_outra_proposta(monkeypatch):
    monkeypatch.setenv("CTI_DOCUMENT_PREVIEW_SECRET", "segredo-de-teste-cti")
    monkeypatch.setattr(modulo.time, "time", lambda: 1_000)
    expira_em = 1_200
    assinatura = modulo._assinatura("proposta-1", expira_em)
    with pytest.raises(HTTPException) as erro:
        modulo._validar_assinatura("proposta-2", expira_em, assinatura)
    assert erro.value.status_code == 403


def test_assinatura_expirada_e_bloqueada(monkeypatch):
    monkeypatch.setenv("CTI_DOCUMENT_PREVIEW_SECRET", "segredo-de-teste-cti")
    monkeypatch.setattr(modulo.time, "time", lambda: 2_000)
    expira_em = 1_999
    assinatura = modulo._assinatura("proposta-1", expira_em)
    with pytest.raises(HTTPException) as erro:
        modulo._validar_assinatura("proposta-1", expira_em, assinatura)
    assert erro.value.status_code == 403


def test_assinatura_com_validade_excessiva_e_bloqueada(monkeypatch):
    monkeypatch.setenv("CTI_DOCUMENT_PREVIEW_SECRET", "segredo-de-teste-cti")
    monkeypatch.setattr(modulo.time, "time", lambda: 1_000)
    expira_em = 2_000
    assinatura = modulo._assinatura("proposta-1", expira_em)
    with pytest.raises(HTTPException) as erro:
        modulo._validar_assinatura("proposta-1", expira_em, assinatura)
    assert erro.value.status_code == 403
