from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core import admin_auth


class _Query:
    def __init__(self, data):
        self._data = data

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        return SimpleNamespace(data=self._data)


class _Auth:
    def __init__(self, user=None, error=None):
        self.user = user
        self.error = error

    def get_user(self, _token):
        if self.error:
            raise self.error
        return SimpleNamespace(user=self.user)


class _Supabase:
    def __init__(self, user=None, profile=None, auth_error=None):
        self.auth = _Auth(user=user, error=auth_error)
        self.profile = profile

    def table(self, name):
        assert name == "cti_users"
        return _Query(self.profile)


def _credenciais():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-valido")


def test_usuario_atual_exige_bearer():
    with pytest.raises(HTTPException) as exc:
        admin_auth.usuario_atual(None)
    assert exc.value.status_code == 401


def test_usuario_atual_rejeita_token_invalido(monkeypatch):
    monkeypatch.setattr(admin_auth, "supabase", _Supabase(auth_error=RuntimeError("token inválido")))
    with pytest.raises(HTTPException) as exc:
        admin_auth.usuario_atual(_credenciais())
    assert exc.value.status_code == 401


def test_usuario_atual_rejeita_perfil_inativo(monkeypatch):
    user = SimpleNamespace(id="auth-1", email="usuario@cti.com")
    profile = {
        "id": "user-1",
        "auth_id": "auth-1",
        "nome": "Usuário",
        "email": "usuario@cti.com",
        "tipo_usuario": "ADMIN_MASTER",
        "ativo": False,
    }
    monkeypatch.setattr(admin_auth, "supabase", _Supabase(user=user, profile=profile))
    with pytest.raises(HTTPException) as exc:
        admin_auth.usuario_atual(_credenciais())
    assert exc.value.status_code == 403


def test_admin_master_pode_ler_e_escrever(monkeypatch):
    user = SimpleNamespace(id="auth-1", email="admin@cti.com")
    profile = {
        "id": "user-1",
        "auth_id": "auth-1",
        "nome": "Admin",
        "email": "admin@cti.com",
        "tipo_usuario": "ADMIN_MASTER",
        "ativo": True,
    }
    monkeypatch.setattr(admin_auth, "supabase", _Supabase(user=user, profile=profile))
    autenticado = admin_auth.usuario_atual(_credenciais())
    assert admin_auth.exigir_leitura_catalogo(autenticado) == autenticado
    assert admin_auth.exigir_escrita_catalogo(autenticado) == autenticado


def test_diretor_pode_ler_mas_nao_escrever():
    usuario = admin_auth.UsuarioAutenticado(
        id="user-2",
        auth_id="auth-2",
        email="diretor@cti.com",
        nome="Diretor",
        tipo_usuario="DIRETOR",
    )
    assert admin_auth.exigir_leitura_catalogo(usuario) == usuario
    with pytest.raises(HTTPException) as exc:
        admin_auth.exigir_escrita_catalogo(usuario)
    assert exc.value.status_code == 403


def test_vendedor_nao_pode_ler_catalogo():
    usuario = admin_auth.UsuarioAutenticado(
        id="user-3",
        auth_id="auth-3",
        email="vendedor@cti.com",
        nome="Vendedor",
        tipo_usuario="VENDEDOR",
    )
    with pytest.raises(HTTPException) as exc:
        admin_auth.exigir_leitura_catalogo(usuario)
    assert exc.value.status_code == 403
