from fastapi.testclient import TestClient

from main import app
from routers import modulos_router

client = TestClient(app)


def test_empresas_consolida_campo_canonico_e_legado(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [
            {
                "empresa": "Empresa Alfa",
                "origem_base": "BRASIL",
                "estado": "SP",
                "cidade": "Campinas",
                "linha": "VECTOR 8500",
                "status": "GANHO",
                "valor": 1000,
            },
            {
                "cliente": "Empresa Alfa",
                "origem_base": "BRASIL",
                "estado": "RJ",
                "cidade": "Rio de Janeiro",
                "linha": "SUPRA 850",
                "status": "ABERTO",
                "valor": 500,
            },
            {
                "transportadora": "Operador Beta",
                "origem_base": "VIENA_SP",
                "autorizado": "VIENA",
                "valor": None,
            },
        ],
    )

    response = client.get("/modulos/empresas")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["nome"] == "Empresa Alfa"
    assert body[0]["quantidade_registros"] == 2
    assert body[0]["valor_total"] == 1500
    assert body[1]["nome"] == "Operador Beta"
    assert body[1]["valor_total"] == 0


def test_transportadoras_permanece_alias_compativel(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [{"cliente": "Empresa Legada", "valor": 10}],
    )

    response = client.get("/modulos/transportadoras")

    assert response.status_code == 200
    assert response.json()[0]["nome"] == "Empresa Legada"


def test_empresas_retorna_vazio(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [{"linha": "VECTOR 8500"}],
    )

    response = client.get("/modulos/empresas")

    assert response.status_code == 200
    assert response.json() == []


def test_equipamentos_filtram_slugs_e_agregam_empresas(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [
            {
                "empresa": "Empresa Trailer",
                "estado": "SP",
                "linha": "VECTOR 8500",
                "implementadora": "Implementadora A",
                "valor": 2000,
            },
            {
                "cliente": "Empresa Truck",
                "estado": "MG",
                "linha": "SUPRA 850",
                "implementadora": "Implementadora B",
                "valor": 3000,
            },
            {
                "razao_social": "Empresa Direct",
                "estado": "PR",
                "linha": "CITIMAX 500",
                "implementadora": "Implementadora C",
                "valor": 4000,
            },
        ],
    )

    trailer = client.get("/modulos/equipamentos/trailer")
    diesel = client.get("/modulos/equipamentos/diesel-truck")
    direct = client.get("/modulos/equipamentos/direct-drive")

    assert trailer.status_code == 200
    assert trailer.json()["total_registros"] == 1
    assert trailer.json()["empresas"][0]["nome"] == "Empresa Trailer"

    assert diesel.status_code == 200
    assert diesel.json()["total_registros"] == 1
    assert diesel.json()["empresas"][0]["nome"] == "Empresa Truck"

    assert direct.status_code == 200
    assert direct.json()["total_registros"] == 1
    assert direct.json()["empresas"][0]["nome"] == "Empresa Direct"


def test_equipamento_slug_invalido(monkeypatch):
    monkeypatch.setattr(modulos_router.repository, "buscar_cti_anfir", lambda: [])

    response = client.get("/modulos/equipamentos/invalido")

    assert response.status_code == 404


def test_contexto_operacional_filtra_brasil_e_viena(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [
            {"empresa": "Empresa Brasil", "origem_base": "BRASIL", "valor": 100},
            {"empresa": "Empresa Viena", "origem_base": "VIENA_SP", "autorizado": "VIENA", "valor": 200},
        ],
    )

    brasil = client.get("/modulos/empresas?contexto=brasil")
    viena = client.get("/modulos/empresas?contexto=viena-sp")

    assert brasil.status_code == 200
    assert {item["nome"] for item in brasil.json()} == {"Empresa Brasil", "Empresa Viena"}
    assert viena.status_code == 200
    assert [item["nome"] for item in viena.json()] == ["Empresa Viena"]


def test_contexto_operacional_filtra_equipamentos(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [
            {"empresa": "Trailer Brasil", "origem_base": "BRASIL", "linha": "VECTOR 8500", "valor": 100},
            {"empresa": "Trailer Viena", "origem_base": "VIENA_SP", "autorizado": "VIENA", "linha": "VECTOR 8500", "valor": 200},
        ],
    )

    response = client.get("/modulos/equipamentos/trailer?contexto=viena-sp")

    assert response.status_code == 200
    assert response.json()["total_registros"] == 1
    assert response.json()["empresas"][0]["nome"] == "Trailer Viena"
