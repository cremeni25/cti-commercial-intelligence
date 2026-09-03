from core.admin_auth import UsuarioAutenticado
from routers.crm_scope_clientes_router import _cliente_no_escopo, _visao_total
from routers.crm_scope_router import _usa_escopo_proprio, _visao_consolidada


def usuario(tipo: str, user_id: str = "u1", acesso_total: bool = False) -> UsuarioAutenticado:
    return UsuarioAutenticado(
        id=user_id,
        auth_id=f"auth-{user_id}",
        email=f"{user_id}@cti.local",
        nome=user_id,
        tipo_usuario=tipo,
        permissoes={"acesso_total": acesso_total},
    )


def test_somente_admin_master_e_diretor_com_acesso_total_tem_visao_consolidada():
    assert _visao_consolidada(usuario("ADMIN_MASTER"))
    assert _visao_consolidada(usuario("DIRETOR_VIENA_SP", acesso_total=True))
    assert not _visao_consolidada(usuario("REPRES_REGIAO_01"))
    assert not _visao_consolidada(usuario("REPRES_REGIAO_02"))
    assert not _visao_consolidada(usuario("INDICADOR_VIENA_SP"))
    assert not _visao_consolidada(usuario("USUARIO_CTI"))


def test_qualquer_usuario_nao_consolidado_usa_escopo_proprio():
    for tipo in ("REPRES_REGIAO_01", "REPRES_REGIAO_02", "INDICADOR_VIENA_SP", "USUARIO_CTI", "ADMIN_COMERCIAL_VIENA_SP"):
        assert _usa_escopo_proprio(usuario(tipo))


def test_cliente_com_responsavel_explicito_nunca_vaza_para_outro_usuario():
    comercial = usuario("USUARIO_CTI", "u1")
    assert _cliente_no_escopo({"responsavel_comercial_id": "u1"}, comercial)
    assert not _cliente_no_escopo({"responsavel_comercial_id": "u2"}, comercial)


def test_visao_total_clientes_permanece_exclusiva_da_gestao():
    assert _visao_total(usuario("ADMIN_MASTER"))
    assert _visao_total(usuario("DIRETOR_VIENA_SP", acesso_total=True))
    assert not _visao_total(usuario("USUARIO_CTI", acesso_total=False))
