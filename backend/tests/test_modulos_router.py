from fastapi.testclient import TestClient

from main import app
from routers import modulos_router

client = TestClient(app)


def test_transportadoras_consolida_clientes(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [
            {
                "cliente": "Trans Alfa",
                "estado": "SP",
                "cidade": "Campinas",
                "linha": "VECTOR 8500",
                "status": "GANHO",
                "valor": 1000,
            },
            {
                "cliente": "Trans Alfa",
                "estado": "RJ",
                "cidade": "Rio de Janeiro",
                "linha": "SUPRA 850",
                "status": "ABERTO",
                "valor": 500,
            },
        ],
    )

    response = client.get("/modulos/transportadoras")

    assert response.status_code == 200
    assert response.json()[0]["nome"] == "Trans Alfa"
    assert response.json()[0]["quantidade_registros"] == 2
    assert response.json()[0]["valor_total"] == 1500


def test_equipamento_filtra_por_slug(monkeypatch):
    monkeypatch.setattr(
        modulos_router.repository,
        "buscar_cti_anfir",
        lambda: [
            {
                "cliente": "Cliente Trailer",
                "estado": "SP",
                "linha": "VECTOR 8500",
                "implementadora": "Implementadora A",
                "valor": 2000,
            },
            {
                "cliente": "Cliente Truck",
                "estado": "MG",
                "linha": "SUPRA 850",
                "implementadora": "Implementadora B",
                "valor": 3000,
            },
        ],
    )

    response = client.get("/modulos/equipamentos/trailer")

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "trailer"
    assert body["total_registros"] == 1
    assert body["valor_total"] == 2000
    assert body["linhas"][0]["nome"] == "VECTOR 8500"
