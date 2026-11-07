"""Resumo diário no celular: cofre auto-provisionado, escopo, entrega e disparo OIDC."""
import json
import time
from datetime import date
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from core import application_access, github_oidc
from core.admin_auth import usuario_atual
from main import app
from services import cofre_agente as cofre
from services import notificacoes_push as push
from services.inteligencia_comercial import servico
from services.inteligencia_comercial import feedback as fb
from tests import cofre_falso

HOJE = date(2026, 11, 9)


def _op(oid, responsavel):
    return {"oportunidade_id": oid, "cliente_id": f"cli-{oid}", "cliente_nome": f"Frigorífico {oid}", "responsavel_id": responsavel,
            "etapa": "ATIVIDADE", "valor": 750000.0, "probabilidade": 40, "data_fechamento_prevista": "2026-10-01",
            "created_at": "2026-11-01T00:00:00+00:00", "updated_at": "2026-11-05T00:00:00+00:00", "linha_equipamento": "TRAILER"}


def _assinatura(nome):
    return {"endpoint": f"https://push.exemplo/{nome}", "keys": {"p256dh": "k", "auth": "a"}}


@pytest.fixture
def ambiente(monkeypatch):
    storage = cofre_falso.instalar(monkeypatch)
    usuarios = [
        {"id": "vend-1", "tipo_usuario": "REPRES_REGIAO_01", "ativo": True},
        {"id": "vend-2", "tipo_usuario": "REPRES_REGIAO_02", "ativo": True},
        {"id": "master", "tipo_usuario": "ADMIN_MASTER", "ativo": True},
        {"id": "inativo", "tipo_usuario": "REPRES_REGIAO_01", "ativo": False},
    ]
    tabela = SimpleNamespace(select=lambda *_: SimpleNamespace(execute=lambda: SimpleNamespace(data=usuarios)))
    monkeypatch.setattr("core.supabase_client.supabase", SimpleNamespace(table=lambda nome: tabela))
    monkeypatch.setattr("core.admin_auth._buscar_permissoes", lambda user_id, tipo: {"acesso_total": True} if tipo == "ADMIN_MASTER" else {"oportunidades_visualizar": True})
    monkeypatch.setattr(servico, "_carregar_oportunidades", lambda: [_op("A", "vend-1")])  # vend-2 sem negócios
    monkeypatch.setattr(servico, "_carregar_atividades", lambda: [])
    monkeypatch.setattr(servico, "_carregar_feedback", lambda hoje: [])
    for usuario in ("vend-1", "vend-2", "master", "inativo"):
        push.salvar_assinatura(usuario, _assinatura(usuario))
    return storage


def test_cofre_e_bucket_privado_criados_automaticamente(ambiente):
    assert "cti-agente" in ambiente.buckets and ambiente.publicos["cti-agente"] is False
    with pytest.raises(ValueError):
        cofre.caminho("push", "../segredo.json")


def test_chaves_vapid_geradas_uma_vez_e_reaproveitadas(ambiente, monkeypatch):
    primeira = push.chaves_vapid()
    monkeypatch.setattr(push, "_CHAVES_CACHE", None)
    assert push.chaves_vapid() == primeira  # relida do cofre, não regenerada
    assert len(primeira["publica"]) == 87 and push.push_configurado()
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "pub-env")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "priv-env")
    assert push.chaves_vapid() == {"publica": "pub-env", "privada": "priv-env"}


def test_mesmo_aparelho_com_outra_pessoa_muda_de_dono(ambiente):
    push.salvar_assinatura("vend-2", _assinatura("vend-1"))
    donos = {a["usuario_id"] for a in push.assinaturas_ativas() if a["endpoint"] == "https://push.exemplo/vend-1"}
    assert donos == {"vend-2"}


def test_mensagem_sem_valores_e_vazia_sem_prioridades():
    briefing = {"manchete": "Você tem R$ 1,2 mi em risco.", "prioridades": [{"titulo": "Negócio parado há 30 dias: Frigorífico A"}, {"titulo": "x"}]}
    mensagem = push.mensagem_do_briefing(briefing)
    assert mensagem["title"] == "Seu dia comercial · 2 prioridades"
    assert mensagem["body"] == "Comece por: Negócio parado há 30 dias: Frigorífico A"
    assert "R$" not in mensagem["body"] and mensagem["url"] == "/crm-app/prioridades"
    assert push.mensagem_do_briefing({"prioridades": []}) is None


def test_resumo_respeita_escopo_inatividade_e_envia_uma_vez_por_dia(ambiente):
    enviados = []
    relatorio = push.enviar_resumo_diario(hoje=HOJE, enviar=lambda assinatura, mensagem: enviados.append(assinatura["usuario_id"]))
    assert sorted(enviados) == ["master", "vend-1"]
    assert relatorio["ignorados"] == 1 and relatorio["sem_prioridades"] == 1 and relatorio["notificados"] == 2
    repetido = push.enviar_resumo_diario(hoje=HOJE, enviar=lambda a, m: enviados.append("duplicado"))
    assert repetido == {"data": HOJE.isoformat(), "ja_enviado": True} and "duplicado" not in enviados


def test_assinatura_expirada_e_desativada(ambiente):
    class Expirada(Exception):
        response = SimpleNamespace(status_code=410)

    def enviar(assinatura, mensagem):
        if assinatura["usuario_id"] == "vend-1":
            raise Expirada()

    relatorio = push.enviar_resumo_diario(hoje=HOJE, enviar=enviar)
    assert relatorio["desativadas"] == 1
    assert "vend-1" not in {a["usuario_id"] for a in push.assinaturas_ativas()}


def test_validacao_de_assinatura():
    with pytest.raises(ValueError):
        push.validar_assinatura({"endpoint": "http://inseguro", "keys": {"p256dh": "a", "auth": "b"}})
    with pytest.raises(ValueError):
        push.validar_assinatura({"endpoint": "https://ok.exemplo/x", "keys": {}})


def test_feedback_no_cofre_com_retencao(ambiente):
    fb.registrar_feedback(usuario_id="vend-1", codigo="X", entidade_tipo="oportunidade", entidade_id="A", decisao="ADIAR",
                          motivo="JA_TRATADO", observacao=None, hoje=HOJE, adiar_ate=date(2026, 11, 20))
    registros = fb.carregar_feedback(desde=date(2026, 11, 1))
    assert len(registros) == 1 and registros[0]["suprimir_ate"] == "2026-11-20"
    assert fb.supressoes_ativas(registros, HOJE) == {("X", "oportunidade", "A")}


@pytest.fixture
def http(ambiente, monkeypatch):
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


def test_http_config_gera_chave_e_inscricao_do_proprio_aparelho(http):
    config = http.get("/crm-seguro/notificacoes/config").json()
    assert config["disponivel"] is True and len(config["chave_publica"]) == 87
    assert http.post("/crm-seguro/notificacoes/assinatura", json=_assinatura("novo")).status_code == 201
    assert "https://push.exemplo/novo" in {a["endpoint"] for a in push.assinaturas_ativas("vend-1")}
    assert http.post("/crm-seguro/notificacoes/assinatura/remover", json={"endpoint": "https://push.exemplo/novo"}).status_code == 200
    assert "https://push.exemplo/novo" not in {a["endpoint"] for a in push.assinaturas_ativas("vend-1")}
    http.post("/crm-seguro/notificacoes/assinatura/remover", json={"endpoint": "https://push.exemplo/vend-2"})
    assert push.assinaturas_ativas("vend-2"), "não remove aparelho de outro usuário"


def test_http_cofre_fora_do_ar_responde_503(http, monkeypatch):
    monkeypatch.setattr(push, "_CHAVES_CACHE", None)
    monkeypatch.setattr(cofre, "ler", lambda *a, **k: (_ for _ in ()).throw(cofre.CofreIndisponivel("fora")))
    assert http.get("/crm-seguro/notificacoes/config").json()["disponivel"] is False


# ---- Disparo agendado autenticado por OIDC do GitHub (sem segredo) ----

CHAVE_GITHUB = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _token(**alteracoes):
    agora = int(time.time())
    claims = {"iss": github_oidc.EMISSOR, "aud": "cti-resumo-diario", "iat": agora, "exp": agora + 300,
              "repository": "cremeni25/cti-commercial-intelligence", "ref": "refs/heads/main", "event_name": "schedule",
              "workflow_ref": "cremeni25/cti-commercial-intelligence/.github/workflows/resumo-diario.yml@refs/heads/main"}
    claims.update(alteracoes)
    return jwt.encode(claims, CHAVE_GITHUB, algorithm="RS256", headers={"kid": "teste"})


@pytest.fixture
def disparo(ambiente, monkeypatch):
    monkeypatch.setattr(github_oidc, "_chave_assinatura", lambda token: CHAVE_GITHUB.public_key())
    monkeypatch.setattr(push, "_enviar_push", lambda assinatura, mensagem: None)
    monkeypatch.delenv("CTI_CRON_TOKEN", raising=False)
    monkeypatch.setattr("services.inteligencia_comercial.briefing.hoje_operacional", lambda: HOJE)
    with TestClient(app) as client:
        yield client


def _post(client, token):
    return client.post("/interno/notificacoes/resumo-diario", headers={"Authorization": f"Bearer {token}"})


def test_oidc_do_workflow_oficial_dispara_uma_vez(disparo):
    resposta = _post(disparo, _token())
    assert resposta.status_code == 200 and resposta.json()["notificados"] == 2
    assert _post(disparo, _token()).json()["ja_enviado"] is True


@pytest.mark.parametrize("alteracao", [
    {"repository": "atacante/fork"},
    {"ref": "refs/heads/feature"},
    {"workflow_ref": "cremeni25/cti-commercial-intelligence/.github/workflows/outro.yml@refs/heads/main"},
    {"event_name": "pull_request"},
    {"aud": "outro-publico"},
    {"iss": "https://emissor.falso"},
    {"exp": int(time.time()) - 3600},
])
def test_oidc_rejeita_qualquer_desvio(disparo, alteracao):
    assert _post(disparo, _token(**alteracao)).status_code == 401


def test_oidc_rejeita_assinatura_de_outra_chave(disparo):
    outra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    claims = json.loads(json.dumps(jwt.decode(_token(), options={"verify_signature": False})))
    assert _post(disparo, jwt.encode(claims, outra, algorithm="RS256")).status_code == 401


def test_sem_credencial_nao_dispara_e_demais_rotas_seguem_protegidas(disparo):
    assert disparo.post("/interno/notificacoes/resumo-diario").status_code == 401
    assert disparo.get("/crm-seguro/notificacoes/config").status_code == 401
