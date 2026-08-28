from types import SimpleNamespace

import routers.crm_scope_clientes_router as clientes_scope
import routers.crm_scope_empresas_router as empresas_scope


def usuario_regional():
    return SimpleNamespace(
        id="user-monica",
        tipo_usuario="REPRES_REGIAO_01",
        permissoes={"clientes_visualizar": True, "clientes_editar": False},
        ddds=["011", "012"],
        nome="Monica",
    )


def test_catalogo_clientes_permanece_global_para_pesquisa(monkeypatch):
    base = [
        {"id": "c1", "nome": "Cliente da carteira A", "cnpj": "11111111000111"},
        {"id": "c2", "nome": "Empresa ainda sem negocio", "cnpj": "22222222000122"},
    ]
    monkeypatch.setattr(clientes_scope, "listar_clientes_crm_app", lambda: base)

    assert clientes_scope.listar_clientes_seguro(usuario_regional()) == base


def test_crm_resumo_aplica_filtro_de_responsabilidade(monkeypatch):
    usuario = usuario_regional()
    oportunidades = [
        {"id": "o1", "responsavel_id": "user-monica"},
        {"id": "o2", "responsavel_id": "outro-user"},
    ]
    propostas = [
        {"id": "p1", "responsavel_id": "user-monica"},
        {"id": "p2", "responsavel_id": "outro-user"},
    ]
    pedidos = [
        {"id": "pd1", "responsavel_id": "user-monica"},
        {"id": "pd2", "responsavel_id": "outro-user"},
    ]
    agenda = {"itens": [
        {"id": "a1", "usuario_id": "user-monica"},
        {"id": "a2", "usuario_id": "outro-user"},
    ]}

    monkeypatch.setattr(empresas_scope, "listar_oportunidades", lambda: oportunidades)
    monkeypatch.setattr(empresas_scope, "listar_propostas_operacionais", lambda: propostas)
    monkeypatch.setattr(empresas_scope, "listar_pedidos_operacionais", lambda: pedidos)
    monkeypatch.setattr(empresas_scope, "agenda_comercial", lambda: agenda)
    monkeypatch.setattr(
        empresas_scope,
        "_filtrar_por_usuario",
        lambda registros, u: [r for r in registros if r.get("responsavel_id") == u.id],
    )
    monkeypatch.setattr(
        empresas_scope,
        "_filtrar_agenda",
        lambda bruto, u: {"itens": [r for r in bruto["itens"] if r.get("usuario_id") == u.id]},
    )

    resultado = empresas_scope.crm_resumo_seguro(usuario)

    assert [r["id"] for r in resultado["oportunidades"]] == ["o1"]
    assert [r["id"] for r in resultado["propostas"]] == ["p1"]
    assert [r["id"] for r in resultado["pedidos"]] == ["pd1"]
    assert [r["id"] for r in resultado["atividades"]] == ["a1"]
