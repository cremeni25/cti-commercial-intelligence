import os
from copy import deepcopy

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")

from fastapi.testclient import TestClient
from main import app
from routers import crm_router


class Result:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, db, table):
        self.db = db
        self.table = table
        self.action = "select"
        self.payload = None
        self.filters = []

    def select(self, *_args):
        self.action = "select"
        return self

    def order(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def delete(self):
        self.action = "delete"
        return self

    def _records(self):
        records = self.db.setdefault(self.table, [])
        for field, value in self.filters:
            records = [record for record in records if record.get(field) == value]
        return records

    def execute(self):
        if self.action == "insert":
            record = deepcopy(self.payload)
            record.setdefault("id", f"{self.table}-{len(self.db.setdefault(self.table, [])) + 1}")
            record.setdefault("created_at", "2026-07-18T00:00:00Z")
            self.db[self.table].append(record)
            return Result([record])
        if self.action == "update":
            updated = []
            for record in self.db.setdefault(self.table, []):
                if all(record.get(field) == value for field, value in self.filters):
                    record.update(self.payload)
                    updated.append(deepcopy(record))
            return Result(updated)
        if self.action == "delete":
            self.db[self.table] = [
                record for record in self.db.setdefault(self.table, [])
                if not all(record.get(field) == value for field, value in self.filters)
            ]
            return Result([])
        return Result(deepcopy(self._records()))


class FakeSupabase:
    def __init__(self):
        self.db = {
            "cti_oportunidades": [],
            "cti_pipeline": [],
            "cti_propostas": [],
            "cti_pedidos": [],
            "cti_atividades": [],
        }

    def table(self, name):
        return Query(self.db, name)


def client_with_fake(monkeypatch):
    fake = FakeSupabase()
    monkeypatch.setattr(crm_router, "supabase", fake)
    return TestClient(app), fake


def test_criacao_leitura_atualizacao_oportunidade_e_404(monkeypatch):
    client, _fake = client_with_fake(monkeypatch)

    created = client.post("/crm/oportunidades", json={
        "cliente_id": "empresa-1", "responsavel_id": "user-1", "titulo": "Retrofit", "valor_estimado": 1000, "probabilidade": 50
    })
    assert created.status_code == 200
    oportunidade_id = created.json()[0]["id"]

    read = client.get(f"/crm/oportunidades/{oportunidade_id}")
    assert read.status_code == 200
    assert read.json()["cliente_id"] == "empresa-1"

    updated = client.put(f"/crm/oportunidades/{oportunidade_id}", json={"status": "NEGOCIACAO", "probabilidade": 75})
    assert updated.status_code == 200
    assert updated.json()[0]["status"] == "NEGOCIACAO"

    missing = client.get("/crm/oportunidades/inexistente")
    assert missing.status_code == 404


def test_pipeline_muda_fase_e_persiste_na_oportunidade(monkeypatch):
    client, _fake = client_with_fake(monkeypatch)
    oportunidade_id = client.post("/crm/oportunidades", json={
        "cliente_id": "empresa-1", "responsavel_id": "user-1", "titulo": "Venda", "status": "PROSPECCAO"
    }).json()[0]["id"]
    pipeline_id = client.post("/crm/pipeline", json={
        "oportunidade_id": oportunidade_id, "etapa": "PROSPECCAO", "usuario_id": "user-1"
    }).json()[0]["id"]

    moved = client.put(f"/crm/pipeline/{pipeline_id}", json={"etapa": "GANHO"})
    assert moved.status_code == 200
    assert moved.json()[0]["etapa"] == "GANHO"
    assert client.get(f"/crm/oportunidades/{oportunidade_id}").json()["status"] == "GANHO"

    pipeline = client.get("/crm/pipeline")
    assert pipeline.status_code == 200
    assert pipeline.json()[0]["id"] == pipeline_id
    assert pipeline.json()[0]["etapa"] == "GANHO"


def test_pipeline_lista_linhas_reais_e_preserva_historico(monkeypatch):
    client, _fake = client_with_fake(monkeypatch)
    oportunidade_id = client.post("/crm/oportunidades", json={
        "cliente_id": "empresa-1", "responsavel_id": "user-1", "titulo": "Venda", "status": "PROSPECCAO"
    }).json()[0]["id"]
    primeira = client.post("/crm/pipeline", json={
        "oportunidade_id": oportunidade_id, "etapa": "PROSPECCAO", "usuario_id": "user-1", "observacao": "entrada"
    }).json()[0]
    segunda = client.post("/crm/pipeline", json={
        "oportunidade_id": oportunidade_id, "etapa": "NEGOCIACAO", "usuario_id": "user-2", "observacao": "avanco"
    }).json()[0]

    pipeline = client.get("/crm/pipeline")

    assert pipeline.status_code == 200
    assert len(pipeline.json()) == 2
    assert {item["id"] for item in pipeline.json()} == {primeira["id"], segunda["id"]}
    assert {item["usuario_id"] for item in pipeline.json()} == {"user-1", "user-2"}
    assert {item["observacao"] for item in pipeline.json()} == {"entrada", "avanco"}

    atualizada = client.put(f"/crm/pipeline/{primeira['id']}", json={"etapa": "GANHO", "observacao": "fechamento"})

    assert atualizada.status_code == 200
    assert atualizada.json()[0]["id"] == primeira["id"]
    assert atualizada.json()[0]["observacao"] == "fechamento"
    assert client.get(f"/crm/oportunidades/{oportunidade_id}").json()["status"] == "GANHO"
    assert len(client.get("/crm/pipeline").json()) == 2


def test_relacionamentos_proposta_pedido_e_atividade(monkeypatch):
    client, _fake = client_with_fake(monkeypatch)
    oportunidade_id = client.post("/crm/oportunidades", json={
        "cliente_id": "empresa-1", "responsavel_id": "user-1", "titulo": "Venda"
    }).json()[0]["id"]
    proposta = client.post("/crm/propostas", json={
        "numero": "P-1", "cliente_id": "empresa-1", "oportunidade_id": oportunidade_id, "valor": 2000, "status": "EM_ANALISE"
    })
    assert proposta.status_code == 200
    proposta_id = proposta.json()[0]["id"]
    assert client.get(f"/crm/propostas/{proposta_id}").json()["oportunidade_id"] == oportunidade_id

    pedido = client.post("/crm/pedidos", json={
        "numero": "PED-1", "cliente_id": "empresa-1", "proposta_id": proposta_id, "oportunidade_id": oportunidade_id, "valor": 2000
    })
    assert pedido.status_code == 200
    assert pedido.json()[0]["proposta_id"] == proposta_id

    atividade = client.post("/crm/atividades", json={
        "cliente_id": "empresa-1", "oportunidade_id": oportunidade_id, "proposta_id": proposta_id, "usuario_id": "user-1", "tipo": "follow-up", "titulo": "Retornar"
    })
    assert atividade.status_code == 200
    atividade_id = atividade.json()[0]["id"]
    concluida = client.put(f"/crm/atividades/{atividade_id}/concluir")
    assert concluida.status_code == 200
    assert concluida.json()[0]["status"] == "CONCLUIDA"


def test_forecast_calcula_probabilidades_percentual_e_decimal(monkeypatch):
    client, fake = client_with_fake(monkeypatch)
    casos_validos = [
        ("zero", 0, 0),
        ("um_decimal", 0.01, 10),
        ("vinte_cinco_decimal", 0.25, 250),
        ("cinquenta_decimal", 0.5, 500),
        ("um_percentual", 1, 10),
        ("cinquenta_percentual", 50, 500),
        ("cem_percentual", 100, 1000),
        ("negativo", -1, 0),
        ("maior_que_cem", 101, 0),
    ]
    for titulo, probabilidade, _ponderado in casos_validos:
        response = client.post("/crm/oportunidades", json={
            "cliente_id": f"empresa-{titulo}",
            "responsavel_id": "user-1",
            "titulo": titulo,
            "valor_estimado": 1000,
            "probabilidade": probabilidade,
            "status": "NEGOCIACAO",
            "data_fechamento_prevista": "2026-08-10",
        })
        assert response.status_code == 200

    casos_legados_invalidos = [
        ("string_invalida", "abc", 0),
        ("nulo", None, 0),
    ]
    for titulo, probabilidade, _ponderado in casos_legados_invalidos:
        fake.db["cti_oportunidades"].append({
            "id": f"legado-{titulo}",
            "cliente_id": f"empresa-{titulo}",
            "responsavel_id": "user-1",
            "titulo": titulo,
            "valor_estimado": 1000,
            "probabilidade": probabilidade,
            "status": "NEGOCIACAO",
            "data_fechamento_prevista": "2026-08-10",
            "created_at": "2026-07-18T00:00:00Z",
        })

    forecast = client.get("/crm/forecast")
    casos = casos_validos + casos_legados_invalidos

    assert forecast.status_code == 200
    assert forecast.json()[0]["pipeline_total"] == 11000
    assert forecast.json()[0]["pipeline_ponderado"] == sum(item[2] for item in casos)
    assert forecast.json()[0]["qtd_oportunidades"] == len(casos)
