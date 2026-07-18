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
    assert pipeline.json()[0]["etapa"] == "GANHO"


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
    client, _fake = client_with_fake(monkeypatch)
    client.post("/crm/oportunidades", json={
        "cliente_id": "empresa-1", "responsavel_id": "user-1", "titulo": "A", "valor_estimado": 1000, "probabilidade": 50, "status": "NEGOCIACAO", "data_fechamento_prevista": "2026-08-10"
    })
    client.post("/crm/oportunidades", json={
        "cliente_id": "empresa-2", "responsavel_id": "user-1", "titulo": "B", "valor_estimado": 1000, "probabilidade": 0.25, "status": "NEGOCIACAO", "data_fechamento_prevista": "2026-08-20"
    })

    forecast = client.get("/crm/forecast")
    assert forecast.status_code == 200
    assert forecast.json()[0]["pipeline_total"] == 2000
    assert forecast.json()[0]["pipeline_ponderado"] == 750
    assert forecast.json()[0]["qtd_oportunidades"] == 2
