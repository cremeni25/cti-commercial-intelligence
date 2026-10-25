"""Regressão HTTP: router real do CTI com transporte de dados isolado."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core.admin_auth import usuario_atual
from core import application_access
from main import app
from routers import crm_scope_clientes_router as clientes


@pytest.fixture
def cti(monkeypatch):
    registros = [
        {"id": "a", "nome": "Carteira A", "responsavel_comercial_id": "regional-a"},
        {"id": "b", "nome": "Carteira B", "responsavel_comercial_id": "regional-b"},
        {"id": "c", "nome": "A conferir", "responsavel_comercial_id": None},
    ]
    perfil = SimpleNamespace(id="master", tipo_usuario="ADMIN_MASTER", permissoes={})
    monkeypatch.setattr(application_access, "usuario_atual", lambda *_: perfil)
    monkeypatch.setattr(clientes, "supabase", SimpleNamespace(table=lambda _: SimpleNamespace(
        select=lambda *_: SimpleNamespace(execute=lambda: SimpleNamespace(data=registros)))))
    monkeypatch.setattr(clientes, "_perfil_usuario", lambda id: {"id": id, "nome": id})
    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[usuario_atual] = lambda: perfil
    try:
        with TestClient(app) as client:
            yield client, perfil
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)


def test_clientes_get_e_post_possuem_apenas_um_handler():
    def rotas_efetivas(router):
        for rota in router.routes:
            if hasattr(rota, "original_router"):
                yield from rotas_efetivas(rota.original_router)
            else:
                yield rota

    for metodo in ("GET", "POST"):
        rotas = [r for r in rotas_efetivas(app) if getattr(r, "path", "") == "/crm-seguro/clientes" and metodo in getattr(r, "methods", set())]
        assert len(rotas) == 1
        assert rotas[0].endpoint.__module__ == clientes.__name__


def test_master_filtra_responsavel_e_nao_atribuidos_por_http(cti):
    client, _ = cti
    assert len(client.get("/crm-seguro/clientes").json()) == 3
    resposta = client.get("/crm-seguro/clientes?responsavel_id=regional-b")
    assert resposta.status_code == 200
    assert [r["id"] for r in resposta.json()] == ["b"]
    resposta = client.get("/crm-seguro/clientes?nao_atribuidos=true")
    assert resposta.status_code == 200
    assert [r["id"] for r in resposta.json()] == ["c"]


def test_regional_so_recebe_sua_carteira_e_nao_pode_alterar_filtro(cti):
    client, perfil = cti
    perfil.id = "regional-a"
    perfil.tipo_usuario = "REPRES_REGIAO_01"
    perfil.permissoes = {"clientes_visualizar": True}
    resposta = client.get("/crm-seguro/clientes")
    assert resposta.status_code == 200
    assert [r["id"] for r in resposta.json()] == ["a"]
    assert client.get("/crm-seguro/clientes?responsavel_id=regional-b").status_code == 403
    assert client.get("/crm-seguro/clientes?nao_atribuidos=true").status_code == 403


def test_sem_permissao_nao_lista_nem_cadastra_cliente(cti):
    client, perfil = cti
    perfil.tipo_usuario = "USUARIO_CTI"
    assert client.get("/crm-seguro/clientes").status_code == 403
    assert client.post("/crm-seguro/clientes", json={"nome": "Cliente isolado"}).status_code == 403
