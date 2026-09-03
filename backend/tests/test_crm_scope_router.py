import pytest
from fastapi import HTTPException

from core.admin_auth import UsuarioAutenticado
from routers.crm_scope_router import _exigir_acesso, _filtrar_por_usuario, _impedir_transferencia


REGISTROS = [
    {"oportunidade_id": "opp-anderson", "responsavel_id": "anderson"},
    {"oportunidade_id": "opp-monica", "responsavel_id": "monica"},
    {"oportunidade_id": "opp-michele", "responsavel_id": "michele"},
    {"oportunidade_id": "opp-gessica", "responsavel_id": "gessica"},
]


def usuario(user_id: str, perfil: str, **permissoes: bool) -> UsuarioAutenticado:
    return UsuarioAutenticado(
        id=user_id,
        auth_id=f"auth-{user_id}",
        email=f"{user_id}@cti.local",
        nome=user_id,
        tipo_usuario=perfil,
        permissoes=permissoes,
    )


def test_admin_master_recebe_consolidado():
    resultado = _filtrar_por_usuario(REGISTROS, usuario("anderson", "ADMIN_MASTER"))
    assert resultado == REGISTROS


def test_diretor_viena_com_acesso_total_recebe_consolidado():
    resultado = _filtrar_por_usuario(
        REGISTROS,
        usuario("andre", "DIRETOR_VIENA_SP", acesso_total=True),
    )
    assert resultado == REGISTROS


def test_representante_regional_recebe_somente_proprios_negocios():
    resultado = _filtrar_por_usuario(REGISTROS, usuario("monica", "REPRES_REGIAO_01"))
    assert [item["oportunidade_id"] for item in resultado] == ["opp-monica"]


def test_segundo_representante_nao_herda_negocios_da_primeira_regiao():
    resultado = _filtrar_por_usuario(REGISTROS, usuario("michele", "REPRES_REGIAO_02"))
    assert [item["oportunidade_id"] for item in resultado] == ["opp-michele"]


def test_usuario_cti_generico_recebe_somente_proprios_negocios():
    resultado = _filtrar_por_usuario(REGISTROS, usuario("gessica", "USUARIO_CTI"))
    assert [item["oportunidade_id"] for item in resultado] == ["opp-gessica"]


def test_representante_pode_abrir_detalhe_do_proprio_negocio():
    registro = {"id": "opp-monica", "responsavel_id": "monica"}
    assert _exigir_acesso(registro, usuario("monica", "REPRES_REGIAO_01")) == registro


def test_representante_nao_pode_abrir_detalhe_de_outro_responsavel():
    with pytest.raises(HTTPException) as erro:
        _exigir_acesso(
            {"id": "opp-anderson", "responsavel_id": "anderson"},
            usuario("monica", "REPRES_REGIAO_01"),
        )
    assert erro.value.status_code == 404


def test_master_pode_abrir_detalhe_de_qualquer_responsavel():
    registro = {"id": "opp-monica", "responsavel_id": "monica"}
    assert _exigir_acesso(registro, usuario("anderson", "ADMIN_MASTER")) == registro


def test_representante_nao_pode_transferir_registro_para_outro_usuario():
    with pytest.raises(HTTPException) as erro:
        _impedir_transferencia("anderson", usuario("monica", "REPRES_REGIAO_01"))
    assert erro.value.status_code == 403


def test_representante_pode_manter_se_proprio_como_responsavel():
    _impedir_transferencia("monica", usuario("monica", "REPRES_REGIAO_01"))