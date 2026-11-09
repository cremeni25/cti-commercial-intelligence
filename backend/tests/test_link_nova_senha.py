"""Master gera link de nova senha para entregar por WhatsApp (sem depender do e-mail)."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from core.admin_auth import UsuarioAutenticado
from routers import governanca_usuarios_router as gov


def _master(tipo="ADMIN_MASTER", **perm):
    return UsuarioAutenticado(id="m", auth_id="m", email="m@example.invalid", nome="M", tipo_usuario=tipo, permissoes=perm)


@pytest.fixture
def ambiente(monkeypatch):
    usuarios = {
        "v1": {"id": "v1", "email": "Vendedora@Example.invalid", "tipo_usuario": "REPRES_REGIAO_01", "ativo": True, "status_acesso": "ATIVO", "acesso_crm": True},
        "off": {"id": "off", "email": "off@example.invalid", "tipo_usuario": "REPRES_REGIAO_01", "ativo": False, "status_acesso": "INATIVO"},
        "adm": {"id": "adm", "email": "adm@example.invalid", "tipo_usuario": "ADMIN_MASTER", "ativo": True},
    }
    pedidos = []

    class Consulta:
        def select(self, *_):
            return self
        def eq(self, _campo, valor):
            self.valor = valor
            return self
        def single(self):
            return self
        def execute(self):
            return SimpleNamespace(data=usuarios.get(self.valor))

    def gerar(dados):
        pedidos.append(dados)
        return SimpleNamespace(properties=SimpleNamespace(action_link="https://auth.example/verify?token=x"))

    monkeypatch.setattr(gov, "supabase", SimpleNamespace(table=lambda _n: Consulta(), auth=SimpleNamespace(admin=SimpleNamespace(generate_link=gerar))))
    return pedidos


def test_master_gera_link_de_recuperacao_para_o_app(ambiente):
    resposta = gov.gerar_link_nova_senha("v1", _master())
    assert resposta == {"email": "vendedora@example.invalid", "link": "https://auth.example/verify?token=x"}
    assert ambiente[0]["type"] == "recovery" and ambiente[0]["options"]["redirect_to"].endswith("/redefinir-senha?destino=/crm-app/login")


def test_link_bloqueado_para_vendedor_conta_desativada_e_admin_master(ambiente):
    with pytest.raises(HTTPException) as erro:
        gov.gerar_link_nova_senha("v1", _master("REPRES_REGIAO_01"))
    assert erro.value.status_code == 403
    with pytest.raises(HTTPException) as erro:
        gov.gerar_link_nova_senha("off", _master())
    assert erro.value.status_code == 409 and "Reative" in erro.value.detail
    with pytest.raises(HTTPException):
        gov.gerar_link_nova_senha("adm", _master())
    assert ambiente == []
