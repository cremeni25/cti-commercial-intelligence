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


def test_dashboard_analytics_contextualizado(monkeypatch):
    from routers import analytics_router

    class RepoAnalyticsFake:
        def buscar_cti_anfir(self):
            return REGISTROS

        def buscar_por_origem(self, origem_base, autorizado=None):
            return [
                r for r in REGISTROS
                if r.get("origem_base") == origem_base
                and (autorizado is None or r.get("autorizado") == autorizado)
            ]

    monkeypatch.setattr(analytics_router, "repository", RepoAnalyticsFake())
    client = TestClient(app)

    sem_contexto = client.get("/analytics/dashboard")
    brasil = client.get("/analytics/dashboard?contexto=brasil")
    viena = client.get("/analytics/dashboard?contexto=viena-sp")
    invalido = client.get("/analytics/dashboard?contexto=invalido")

    assert sem_contexto.status_code == 200
    assert sem_contexto.json()["total_registros"] == 3
    assert brasil.status_code == 200
    assert brasil.json()["total_registros"] == 3
    assert viena.status_code == 200
    assert viena.json()["total_registros"] == 2
    assert viena.json()["faturamento_total"] == 500
    assert invalido.status_code == 422


def test_upload_recebe_contexto_sem_reclassificar_parser(monkeypatch):
    from routers import upload_router

    relatorio = {
        "arquivo": "teste.xlsx",
        "bases_processadas": {
            "BRASIL": {
                "abas": ["BRASIL"],
                "linhas_lidas": 1,
                "registros_validos": 1,
                "inseridos": 0,
                "atualizados": 0,
                "duplicados_ignorados": 0,
                "erros": 0,
                "erros_por_tipo": {},
                "amostra_erros": [],
            }
        },
    }
    registros = [
        {
            "origem_base": "BRASIL",
            "autorizado": None,
            "cliente": "Cliente Brasil",
            "estado": "SP",
            "cidade": "Sao Paulo",
            "valor": 100,
            "linha": "TRAILER",
            "implementadora": "RANDON",
        }
    ]

    monkeypatch.setattr(
        upload_router,
        "processar_planilha_viena_com_relatorio",
        lambda contents, filename: (registros, relatorio),
    )
    monkeypatch.setattr(
        upload_router.repository,
        "persistir_registros_idempotente",
        lambda registros_base: {
            "tentados": len(registros_base),
            "inseridos": len(registros_base),
            "atualizados": 0,
            "duplicados_ignorados": 0,
            "erros": 0,
            "erros_por_tipo": {},
            "amostra_erros": [],
        },
    )

    client = TestClient(app)
    response = client.post(
        "/upload/anfir/seguro",
        data={"contexto_operacional": "viena-sp"},
        files={"file": ("teste.xlsx", b"conteudo", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contexto_operacional"] == "viena-sp"
    assert "BRASIL" in body["bases_processadas"]
    assert body["status"] == "SUCESSO"
