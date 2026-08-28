from core.admin_auth import UsuarioAutenticado
from routers.crm_scope_router import _filtrar_por_usuario


REGISTROS = [
    {"oportunidade_id": "opp-anderson", "responsavel_id": "anderson"},
    {"oportunidade_id": "opp-monica", "responsavel_id": "monica"},
    {"oportunidade_id": "opp-michele", "responsavel_id": "michele"},
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


def test_usuario_cti_generico_preserva_regra_atual_ate_definicao_especifica():
    resultado = _filtrar_por_usuario(REGISTROS, usuario("gessica", "USUARIO_CTI"))
    assert resultado == REGISTROS
