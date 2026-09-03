from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routers import crm_scope_clientes_router as modulo


def usuario(tipo="USUARIO_CTI", **permissoes):
    return SimpleNamespace(
        id="user-1",
        tipo_usuario=tipo,
        permissoes=permissoes,
    )


def test_visualizacao_exige_permissao(monkeypatch):
    monkeypatch.setattr(modulo, "obter_cliente_crm_app", lambda cliente_id: {"id": cliente_id, "responsavel_comercial_id": "user-1"})
    with pytest.raises(HTTPException) as erro:
        modulo.obter_cliente_seguro("cliente-1", usuario())
    assert erro.value.status_code == 403


def test_visualizacao_com_permissao_e_responsabilidade_propria(monkeypatch):
    monkeypatch.setattr(modulo, "obter_cliente_crm_app", lambda cliente_id: {"id": cliente_id, "responsavel_comercial_id": "user-1"})
    monkeypatch.setattr(modulo, "_perfil_usuario", lambda user_id: {"id": user_id, "nome": "Usuário 1", "tipo_usuario": "USUARIO_CTI"})
    retorno = modulo.obter_cliente_seguro("cliente-1", usuario(clientes_visualizar=True))
    assert retorno["id"] == "cliente-1"


def test_visualizacao_com_permissao_nao_autoriza_cliente_de_outro_responsavel(monkeypatch):
    monkeypatch.setattr(modulo, "obter_cliente_crm_app", lambda cliente_id: {"id": cliente_id, "responsavel_comercial_id": "user-2"})
    with pytest.raises(HTTPException) as erro:
        modulo.obter_cliente_seguro("cliente-1", usuario(clientes_visualizar=True))
    assert erro.value.status_code == 403


def test_edicao_exige_clientes_editar(monkeypatch):
    monkeypatch.setattr(modulo, "atualizar_cliente_crm_app", lambda cliente_id, dados: {"id": cliente_id})
    dados = modulo.ClienteEdicao(nome="Cliente Teste")
    with pytest.raises(HTTPException) as erro:
        modulo.atualizar_cliente_seguro("cliente-1", dados, usuario(clientes_visualizar=True))
    assert erro.value.status_code == 403


def test_diretor_com_acesso_total_pode_editar(monkeypatch):
    monkeypatch.setattr(modulo, "atualizar_cliente_crm_app", lambda cliente_id, dados: {"id": cliente_id})
    dados = modulo.ClienteEdicao(nome="Cliente Teste")
    retorno = modulo.atualizar_cliente_seguro(
        "cliente-1",
        dados,
        usuario("DIRETOR_VIENA_SP", acesso_total=True),
    )
    assert retorno["id"] == "cliente-1"