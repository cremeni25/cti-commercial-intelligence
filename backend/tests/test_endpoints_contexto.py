import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")

from fastapi.testclient import TestClient

from main import app
from routers import autorizados_router, brasil_router

REGISTROS = [
    {"origem_base": "BRASIL", "implementadora": "RANDON", "cliente": "A", "estado": "SP", "cidade": "Sao Paulo", "valor": 100, "status": "APROVADO", "linha": "TRAILER"},
    {"origem_base": "VIENA_SP", "autorizado": "VIENA", "ano_referencia": 2025, "implementadora": "RANDON", "cliente": "B", "estado": "SP", "cidade": "Campinas", "valor": 200, "status": "PERDIDO", "linha": "TRAILER"},
    {"origem_base": "VIENA_SP", "autorizado": "VIENA", "ano_referencia": 2026, "implementadora": "FACCHINI", "cliente": "C", "estado": "SP", "cidade": "Santos", "valor": 300, "status": "OUTRO", "linha": "TRUCK"},
]


class RepoFake:
    def buscar_por_origem(self, origem_base, autorizado=None):
        return [
            r for r in REGISTROS
            if r.get("origem_base") == origem_base
            and (autorizado is None or r.get("autorizado") == autorizado)
        ]


def test_endpoints_filtram_contexto(monkeypatch):
    fake = RepoFake()
    monkeypatch.setattr(brasil_router, "repository", fake)
    monkeypatch.setattr(autorizados_router, "repository", fake)
    client = TestClient(app)

    brasil = client.get("/brasil/dashboard")
    assert brasil.status_code == 200
    assert brasil.json()["total_registros"] == 1
    assert brasil.json()["faturamento_total"] == 100

    viena = client.get("/autorizados/viena-sp/dashboard")
    assert viena.status_code == 200
    assert viena.json()["total_registros"] == 2
    assert viena.json()["faturamento_total"] == 500

    impl_brasil = client.get("/brasil/implementadoras")
    assert impl_brasil.status_code == 200
    assert len(impl_brasil.json()) == 1

    impl_viena = client.get("/autorizados/viena-sp/implementadoras")
    assert impl_viena.status_code == 200
    assert len(impl_viena.json()) == 2

    historico = client.get("/autorizados/viena-sp/historico")
    assert historico.status_code == 200
    assert historico.json() == [
        {"ano": "2025", "quantidade_registros": 1},
        {"ano": "2026", "quantidade_registros": 1},
    ]
