from routers import clientes_oportunidade_router, crm_app_clientes_edicao_router, crm_scope_clientes_router, crm_scope_cliente_referencia_router


def metodos_por_caminho(router):
    return {
        rota.path: set(rota.methods or set())
        for rota in router.routes
        if hasattr(rota, "path")
    }


def test_leituras_legadas_de_clientes_permanecem_disponiveis():
    rotas_clientes = metodos_por_caminho(clientes_oportunidade_router.router)
    rotas_edicao = metodos_por_caminho(crm_app_clientes_edicao_router.router)

    assert "GET" in rotas_clientes["/crm-app/clientes"]
    assert "GET" in rotas_edicao["/crm-app/clientes/{cliente_id}"]


def test_escritas_legadas_nao_estao_expostas():
    rotas_clientes = metodos_por_caminho(clientes_oportunidade_router.router)
    rotas_edicao = metodos_por_caminho(crm_app_clientes_edicao_router.router)

    assert "/crm-app/cliente-oportunidade" not in rotas_clientes
    assert "POST" not in rotas_clientes.get("/crm-app/clientes", set())
    assert "PUT" not in rotas_edicao.get("/crm-app/clientes/{cliente_id}", set())


def test_escritas_seguras_continuam_expostas():
    rotas_clientes = metodos_por_caminho(crm_scope_clientes_router.router)
    rotas_negocio = metodos_por_caminho(crm_scope_cliente_referencia_router.router)

    assert "POST" in rotas_clientes["/crm-seguro/clientes"]
    assert "PUT" in rotas_clientes["/crm-seguro/clientes/{cliente_id}"]
    assert "POST" in rotas_negocio["/crm-seguro/cliente-oportunidade"]
