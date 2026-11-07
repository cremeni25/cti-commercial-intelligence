"""Resumo diário no celular: mensagem, escopo por perfil, entrega e disparo."""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core import application_access
from core.admin_auth import usuario_atual
from main import app
from services import notificacoes_push as push
from services.inteligencia_comercial import servico

HOJE = date(2026, 11, 9)


def _op(oid, responsavel):
    return {"oportunidade_id": oid, "cliente_id": f"cli-{oid}", "cliente_nome": f"Frigorífico {oid}", "responsavel_id": responsavel,
            "etapa": "ATIVIDADE", "valor": 750000.0, "probabilidade": 40, "data_fechamento_prevista": "2026-10-01",
            "created_at": "2026-11-01T00:00:00+00:00", "updated_at": "2026-11-05T00:00:00+00:00", "linha_equipamento": "TRAILER"}


class Tabela:
    def __init__(self, banco, nome):
        self.banco, self.nome, self.filtros, self.alteracao = banco, nome, [], None
    def select(self, *_): return self
    def eq(self, campo, valor):
        self.filtros.append((campo, valor)); return self
    def update(self, dados):
        self.alteracao = dados; return self
    def upsert(self, dados, on_conflict=None):
        linhas = self.banco[self.nome]
        existente = next((l for l in linhas if l[on_conflict] == dados[on_conflict]), None)
        existente.update(dados) if existente else linhas.append(dict(dados))
        return self
    def execute(self):
        linhas = [l for l in self.banco[self.nome] if all(l.get(c) == v for c, v in self.filtros)]
        if self.alteracao is not None:
            for linha in linhas:
                linha.update(self.alteracao)
        return SimpleNamespace(data=linhas)


@pytest.fixture
def banco(monkeypatch):
    dados = {
        "cti_push_assinaturas": [
            {"endpoint": "https://push.exemplo/vend-1", "p256dh": "k", "auth": "a", "usuario_id": "vend-1", "ativo": True, "falhas": 0},
            {"endpoint": "https://push.exemplo/vend-2", "p256dh": "k", "auth": "a", "usuario_id": "vend-2", "ativo": True, "falhas": 0},
            {"endpoint": "https://push.exemplo/master", "p256dh": "k", "auth": "a", "usuario_id": "master", "ativo": True, "falhas": 0},
            {"endpoint": "https://push.exemplo/inativo", "p256dh": "k", "auth": "a", "usuario_id": "inativo", "ativo": True, "falhas": 0},
        ],
        "cti_users": [
            {"id": "vend-1", "tipo_usuario": "REPRES_REGIAO_01", "ativo": True},
            {"id": "vend-2", "tipo_usuario": "REPRES_REGIAO_02", "ativo": True},
            {"id": "master", "tipo_usuario": "ADMIN_MASTER", "ativo": True},
            {"id": "inativo", "tipo_usuario": "REPRES_REGIAO_01", "ativo": False},
        ],
    }
    monkeypatch.setattr(push, "_supabase", lambda: SimpleNamespace(table=lambda nome: Tabela(dados, nome)))
    monkeypatch.setattr("core.admin_auth._buscar_permissoes", lambda user_id, tipo: {"acesso_total": True} if tipo == "ADMIN_MASTER" else {"oportunidades_visualizar": True})
    monkeypatch.setattr(servico, "_carregar_oportunidades", lambda: [_op("A", "vend-1")])  # vend-2 sem negócios
    monkeypatch.setattr(servico, "_carregar_atividades", lambda: [])
    monkeypatch.setattr(servico, "_carregar_feedback", lambda hoje: [])
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "priv")
    return dados


def test_mensagem_sem_valores_e_vazia_sem_prioridades():
    briefing = {"manchete": "Você tem R$ 1,2 mi em risco.", "prioridades": [{"titulo": "Negócio parado há 30 dias: Frigorífico A"}, {"titulo": "x"}]}
    mensagem = push.mensagem_do_briefing(briefing)
    assert mensagem["title"] == "Seu dia comercial · 2 prioridades"
    assert mensagem["body"] == "Comece por: Negócio parado há 30 dias: Frigorífico A"
    assert "R$" not in mensagem["body"] and mensagem["url"] == "/crm-app/prioridades"
    assert push.mensagem_do_briefing({"prioridades": []}) is None


def test_resumo_respeita_escopo_inatividade_e_ausencia_de_prioridades(banco):
    enviados = []
    relatorio = push.enviar_resumo_diario(hoje=HOJE, enviar=lambda assinatura, mensagem: enviados.append((assinatura["usuario_id"], mensagem)))
    assert sorted(u for u, _ in enviados) == ["master", "vend-1"]
    assert relatorio["ignorados"] == 1 and relatorio["sem_prioridades"] == 1 and relatorio["notificados"] == 2
    assert all("Frigorífico A" in m["body"] for _, m in enviados)


def test_assinatura_expirada_e_desativada(banco):
    class Expirada(Exception):
        response = SimpleNamespace(status_code=410)

    def enviar(assinatura, mensagem):
        if assinatura["usuario_id"] == "vend-1":
            raise Expirada()

    relatorio = push.enviar_resumo_diario(hoje=HOJE, enviar=enviar)
    assert relatorio["desativadas"] == 1
    linha = next(l for l in banco["cti_push_assinaturas"] if l["usuario_id"] == "vend-1")
    assert linha["ativo"] is False


def test_validacao_de_assinatura():
    with pytest.raises(ValueError):
        push.validar_assinatura({"endpoint": "http://inseguro", "keys": {"p256dh": "a", "auth": "b"}})
    with pytest.raises(ValueError):
        push.validar_assinatura({"endpoint": "https://ok.exemplo/x", "keys": {}})


@pytest.fixture
def http(banco, monkeypatch):
    perfil = SimpleNamespace(id="vend-1", tipo_usuario="REPRES_REGIAO_01", permissoes={"oportunidades_visualizar": True})
    monkeypatch.setattr(application_access, "usuario_atual", lambda *_: perfil)
    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[usuario_atual] = lambda: perfil
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)


def test_http_inscricao_e_remocao_do_proprio_aparelho(http, banco):
    assert http.get("/crm-seguro/notificacoes/config").json() == {"disponivel": True, "chave_publica": "pub"}
    corpo = {"endpoint": "https://push.exemplo/novo", "keys": {"p256dh": "k2", "auth": "a2"}}
    assert http.post("/crm-seguro/notificacoes/assinatura", json=corpo).status_code == 201
    novo = next(l for l in banco["cti_push_assinaturas"] if l["endpoint"] == "https://push.exemplo/novo")
    assert novo["usuario_id"] == "vend-1" and novo["ativo"] is True
    assert http.post("/crm-seguro/notificacoes/assinatura/remover", json={"endpoint": "https://push.exemplo/novo"}).status_code == 200
    assert novo["ativo"] is False
    # Não remove aparelho de outro usuário
    http.post("/crm-seguro/notificacoes/assinatura/remover", json={"endpoint": "https://push.exemplo/vend-2"})
    assert next(l for l in banco["cti_push_assinaturas"] if l["usuario_id"] == "vend-2")["ativo"] is True


def test_http_sem_chaves_vapid_responde_503(http, monkeypatch):
    monkeypatch.delenv("VAPID_PRIVATE_KEY")
    assert http.get("/crm-seguro/notificacoes/config").json()["disponivel"] is False
    assert http.post("/crm-seguro/notificacoes/assinatura", json={"endpoint": "https://push.exemplo/x", "keys": {"p256dh": "k", "auth": "a"}}).status_code == 503


def test_disparo_exige_token_proprio_sem_sessao(banco, monkeypatch):
    monkeypatch.setattr(push, "_enviar_push", lambda assinatura, mensagem: None)
    with TestClient(app) as client:
        monkeypatch.delenv("CTI_CRON_TOKEN", raising=False)
        assert client.post("/interno/notificacoes/resumo-diario").status_code == 503
        monkeypatch.setenv("CTI_CRON_TOKEN", "segredo-de-teste")
        assert client.post("/interno/notificacoes/resumo-diario").status_code == 401
        assert client.post("/interno/notificacoes/resumo-diario", headers={"X-CTI-Cron-Token": "errado"}).status_code == 401
        resposta = client.post("/interno/notificacoes/resumo-diario", headers={"X-CTI-Cron-Token": "segredo-de-teste"})
        assert resposta.status_code == 200 and resposta.json()["notificados"] == 2
        # A exceção pública é só esta rota: o resto continua exigindo sessão.
        assert client.get("/crm-seguro/notificacoes/config").status_code == 401
