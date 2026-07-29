from fastapi.testclient import TestClient

from main import app
from routers import negociacoes_router

client = TestClient(app)


class Resultado:
    def __init__(self, data):
        self.data = data


class Consulta:
    def __init__(self, tabela, dados):
        self.tabela = tabela
        self.dados = dados

    def select(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        return Resultado(self.dados[self.tabela])


class SupabaseFake:
    def __init__(self, dados):
        self.dados = dados

    def table(self, tabela):
        return Consulta(tabela, self.dados)


def test_quadro_pipeline_usa_ultima_movimentacao_e_calcula_valores(monkeypatch):
    monkeypatch.setattr(
        negociacoes_router,
        "supabase",
        SupabaseFake({
            "cti_oportunidades": [
                {
                    "id": "opp-1",
                    "titulo": "Renovação de frota",
                    "cliente_id": "CLIENTE ALFA",
                    "status": "OPORTUNIDADE",
                    "origem": "CRM_APP",
                    "valor_estimado": 100000,
                    "probabilidade": 40,
                    "equipamento": "SUPRA 850",
                    "implementadora": "FACCHINI",
                },
                {
                    "id": "opp-2",
                    "titulo": "Novo implemento",
                    "cliente_id": "CLIENTE BETA",
                    "status": "PROPOSTA",
                    "origem": "crm_app",
                    "valor_estimado": 50000,
                    "probabilidade": 0.5,
                },
            ],
            "cti_pipeline": [
                {"id": "mov-2", "oportunidade_id": "opp-1", "nova_etapa": "NEGOCIACAO", "created_at": "2026-07-23T12:00:00"},
                {"id": "mov-1", "oportunidade_id": "opp-1", "nova_etapa": "PROPOSTA", "created_at": "2026-07-22T12:00:00"},
            ],
        }),
    )

    response = client.get("/crm/pipeline/quadro")

    assert response.status_code == 200
    body = response.json()
    assert body["resumo"]["total_oportunidades"] == 2
    assert body["resumo"]["valor_total"] == 150000
    assert body["resumo"]["valor_ponderado"] == 65000
    assert body["resumo"]["por_etapa"]["NEGOCIACAO"] == 1
    assert body["resumo"]["por_etapa"]["PROPOSTA"] == 1
    assert body["cards"][0]["etapa"] == "NEGOCIACAO"
    assert body["cards"][0]["implementadora"] == "FACCHINI"


def test_quadro_pipeline_ignora_origens_legadas_e_movimentacoes_orfas(monkeypatch):
    monkeypatch.setattr(
        negociacoes_router,
        "supabase",
        SupabaseFake({
            "cti_oportunidades": [
                {
                    "id": "opp-real",
                    "titulo": "Proposta Comercial",
                    "origem": "CRM_APP",
                    "status": "OPORTUNIDADE",
                    "valor_estimado": 94000,
                    "probabilidade": 50,
                },
                {
                    "id": "opp-teste",
                    "titulo": "Carga de teste",
                    "origem": "WEB",
                    "status": "PROSPECCAO",
                    "valor_estimado": 2800000,
                    "probabilidade": 40,
                },
            ],
            "cti_pipeline": [
                {"id": "mov-real", "oportunidade_id": "opp-real", "nova_etapa": "OPORTUNIDADE", "created_at": "2026-07-29T04:41:40"},
                {"id": "mov-teste", "oportunidade_id": "opp-teste", "nova_etapa": "PROPOSTA", "created_at": "2026-06-03T00:31:28"},
                {"id": "mov-orfa", "oportunidade_id": "opp-inexistente", "nova_etapa": "PEDIDO", "created_at": "2026-06-01T00:00:00"},
            ],
        }),
    )

    response = client.get("/crm/pipeline/quadro")

    assert response.status_code == 200
    body = response.json()
    assert body["resumo"]["total_oportunidades"] == 1
    assert body["resumo"]["valor_total"] == 94000
    assert body["resumo"]["valor_ponderado"] == 47000
    assert [card["id"] for card in body["cards"]] == ["opp-real"]


def test_quadro_pipeline_retorna_estrutura_vazia(monkeypatch):
    monkeypatch.setattr(
        negociacoes_router,
        "supabase",
        SupabaseFake({"cti_oportunidades": [], "cti_pipeline": []}),
    )

    response = client.get("/crm/pipeline/quadro")

    assert response.status_code == 200
    assert response.json()["cards"] == []
    assert response.json()["resumo"]["total_oportunidades"] == 0
