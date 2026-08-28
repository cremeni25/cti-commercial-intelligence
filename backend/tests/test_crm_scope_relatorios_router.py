from types import SimpleNamespace

import routers.crm_scope_relatorios_router as relatorios


def test_relatorio_regional_filtra_fluxo_comercial(monkeypatch):
    usuario = SimpleNamespace(id="regional-1", tipo_usuario="REPRES_REGIAO_01", permissoes={})
    oportunidades = [{"id": "o1", "responsavel_id": "regional-1"}, {"id": "o2", "responsavel_id": "outro"}]
    propostas = [{"id": "p1", "responsavel_id": "regional-1"}, {"id": "p2", "responsavel_id": "outro"}]
    pedidos = [{"id": "pd1", "responsavel_id": "regional-1"}, {"id": "pd2", "responsavel_id": "outro"}]
    vendas = [{"id": "v1"}]

    monkeypatch.setattr(relatorios, "listar_oportunidades", lambda: oportunidades)
    monkeypatch.setattr(relatorios, "listar_propostas_operacionais", lambda: propostas)
    monkeypatch.setattr(relatorios, "listar_pedidos_operacionais", lambda: pedidos)
    monkeypatch.setattr(relatorios, "_filtrar_por_usuario", lambda itens, u: [i for i in itens if i.get("responsavel_id") == u.id])
    monkeypatch.setattr(relatorios, "listar_vendas_seguras", lambda u: vendas)

    resultado = relatorios.relatorio_comercial_seguro(usuario)

    assert [i["id"] for i in resultado["oportunidades"]] == ["o1"]
    assert [i["id"] for i in resultado["propostas"]] == ["p1"]
    assert [i["id"] for i in resultado["pedidos"]] == ["pd1"]
    assert resultado["vendas"] == vendas
