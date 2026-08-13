import pytest
from fastapi import HTTPException

from routers.crm_app_clientes_edicao_router import ClienteEdicao, _payload
from routers.crm_app_proposta_envio_router import _emails_validos
from routers.crm_app_oportunidade_propostas_envio_router import _emails_validos as _emails_validos_lote


def test_edicao_cliente_normaliza_cadastro_canonico():
    dados = ClienteEdicao(
        nome="  Cliente Teste Ltda  ",
        cnpj="12.345.678/0001-90",
        estado="sp",
        categoria="transportadora",
        ddd="(11)",
        email=" COMERCIAL@EXEMPLO.COM.BR ",
    )
    payload = _payload(dados)
    assert payload["nome"] == "Cliente Teste Ltda"
    assert payload["cnpj"] == "12345678000190"
    assert payload["estado"] == "SP"
    assert payload["categoria"] == "TRANSPORTADORA"
    assert payload["segmento"] == "TRANSPORTADORA"
    assert payload["ddd"] == "11"
    assert payload["email"] == "comercial@exemplo.com.br"


def test_envio_proposta_normaliza_destinatarios_sem_duplicar():
    assert _emails_validos([
        " COMPRAS@CLIENTE.COM.BR ",
        "compras@cliente.com.br",
        "diretoria@cliente.com.br",
    ]) == ["compras@cliente.com.br", "diretoria@cliente.com.br"]


def test_envio_conjunto_normaliza_destinatarios_sem_duplicar():
    assert _emails_validos_lote([
        " COMPRAS@CLIENTE.COM.BR ",
        "compras@cliente.com.br",
        "diretoria@cliente.com.br",
    ]) == ["compras@cliente.com.br", "diretoria@cliente.com.br"]


def test_envio_proposta_rejeita_email_invalido():
    with pytest.raises(HTTPException) as erro:
        _emails_validos(["email-sem-arroba"])
    assert erro.value.status_code == 422


def test_envio_conjunto_rejeita_email_invalido():
    with pytest.raises(HTTPException) as erro:
        _emails_validos_lote(["email-sem-arroba"])
    assert erro.value.status_code == 422
