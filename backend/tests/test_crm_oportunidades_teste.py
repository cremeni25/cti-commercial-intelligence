import pytest
from fastapi import HTTPException

from core.admin_auth import UsuarioAutenticado
from routers.crm_app_oportunidades_teste_router import _admin


def usuario(tipo: str) -> UsuarioAutenticado:
    return UsuarioAutenticado(id="00000000-0000-0000-0000-000000000001", auth_id="auth", email="teste@cti.local", nome="Teste", tipo_usuario=tipo)


def test_arquivamento_restrito_ao_admin_master():
    assert _admin(usuario("ADMIN_MASTER")).tipo_usuario == "ADMIN_MASTER"


def test_arquivamento_rejeita_usuario_comum():
    with pytest.raises(HTTPException) as erro:
        _admin(usuario("USUARIO_CTI"))
    assert erro.value.status_code == 403
