from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import routers.propostas_primeira_pagina_router as primeira_pagina_router
from routers.propostas_primeira_pagina_router import (
    campos_pendentes_documento,
    validar_documento_para_emissao,
)
from routers.cti_api_router import router as cti_router


def _proposta(documento_final: dict | None = None):
    return {"snapshot_dados": {"documento_final": documento_final or {}}}


def _item():
    return {
        "configuracao": "ACOPLADO_E_ELETRICO",
        "opcionais": [],
        "condicao_pagamento": None,
        "local_entrega": None,
        "frete": None,
        "prazo_entrega": None,
        "validade_condicao": None,
    }


def _completo():
    return {
        "voltagem": "12V",
        "tipo_equipamento": "Acoplado e elétrico",
        "impostos": "04% ICMS/PIS/COFINS",
        "condicao_pagamento": "30/60/90 dias",
        "possui_entrada": False,
        "local_entrega": "ENDEREÇO CLIENTE",
        "frete": "CIF",
        "prazo_entrega": "30 dias",
        "validade": "2026-09-30",
    }


def test_campos_obrigatorios_bloqueiam_emissao_incompleta():
    pendentes = campos_pendentes_documento(_proposta(), _item())
    assert "voltagem" in pendentes
    assert "condição de pagamento" in pendentes
    assert "definição de entrada" in pendentes
    assert "validade da proposta" in pendentes

    try:
        validar_documento_para_emissao(_proposta(), _item())
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "Complete os dados do documento oficial" in str(exc.detail)
    else:
        raise AssertionError("Proposta incompleta não poderia ser emitida")


def test_documento_completo_pode_ser_emitido():
    proposta = _proposta(_completo())
    assert campos_pendentes_documento(proposta, _item()) == []
    campos = validar_documento_para_emissao(proposta, _item())
    assert campos["voltagem"] == "12V"
    assert campos["frete"] == "CIF"


def test_regras_condicionais_de_entrada_e_autorizada():
    dados = _completo()
    dados.update({
        "possui_entrada": True,
        "valor_entrada": None,
        "local_entrega": "AUTORIZADA CARRIER",
        "autorizada_nome_endereco": None,
    })
    pendentes = campos_pendentes_documento(_proposta(dados), _item())
    assert "valor da entrada" in pendentes
    assert "nome e endereço da autorizada Carrier" in pendentes


def test_rota_emitir_bloqueia_documento_incompleto(monkeypatch):
    monkeypatch.setattr(primeira_pagina_router, "_contexto", lambda _proposta_id: (_proposta(), _item()))
    app = FastAPI()
    app.include_router(cti_router)
    cliente = TestClient(app, raise_server_exceptions=False)

    resposta = cliente.post("/crm-documentos/propostas/proposta-teste/emitir")

    assert resposta.status_code == 409
    assert "Complete os dados do documento oficial" in resposta.json()["detail"]
