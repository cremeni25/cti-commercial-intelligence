"""Campanhas por grupo da carteira, posts do Canal e autorização LGPD (dados fictícios)."""
from urllib.parse import unquote

import pytest

from services import campanhas_comerciais as campanhas
from tests import cofre_falso
from tests.test_carteira_setorizada import base  # noqa: F401  (fixture)


@pytest.fixture
def ambiente(base, monkeypatch):  # noqa: F811
    for cliente in base["clientes"]:
        cliente["contato"] = "maria souza"
        cliente["fone"] = {"prospect-frota": "(11) 98765-4321", "inativo": "11 3333-4444", "ativo": "123"}.get(cliente["id"])
    cofre_falso.instalar(monkeypatch)
    return base


def test_telefone_whatsapp():
    assert campanhas.telefone_whatsapp("(11) 98765-4321") == "5511987654321"
    assert campanhas.telefone_whatsapp("+55 11 3333-4444") == "551133334444"
    assert campanhas.telefone_whatsapp("123") is None


def test_resumo_publico_e_mensagem_personalizada(ambiente):
    resumo = {c["codigo"]: c for c in campanhas.resumo_campanhas()}
    assert resumo["CONQUISTA_CONCORRENTE"]["total"] == 1 and resumo["CONQUISTA_CONCORRENTE"]["com_whatsapp"] == 1
    assert resumo["REATIVACAO"]["total"] == 1
    assert resumo["RELACIONAMENTO"]["com_whatsapp"] == 0  # telefone inválido
    detalhe = campanhas.publico_detalhado("CONQUISTA_CONCORRENTE")
    gama = detalhe["clientes"][0]
    assert gama["telefone"] == "5511987654321" and gama["autorizacao"] == "PENDENTE"
    assert "Maria" in gama["mensagem"] and "Transportes Gama" in gama["mensagem"] and "25 equipamentos" in gama["mensagem"]
    assert campanhas.TEXTO_AUTORIZACAO in gama["mensagem"]  # pede autorização no primeiro contato
    assert unquote(gama["link_whatsapp"].split("text=")[1]) == gama["mensagem"]
    # o cache da carteira não foi alterado
    from services import carteira_setorizada
    assert "telefone" not in carteira_setorizada.setorizacao()["clientes"][0]


def test_aprovacao_envio_e_autorizacao(ambiente):
    with pytest.raises(ValueError):
        campanhas.marcar_enviado("REATIVACAO", "inativo", "gestor")
    with pytest.raises(ValueError):
        campanhas.salvar_campanha("REATIVACAO", "Mensagem sem o nome da empresa, não personaliza.", True, "gestor")
    with pytest.raises(ValueError):
        campanhas.salvar_campanha("REATIVACAO", "Olá {empresa}, campo {desconhecido} inválido.", True, "gestor")
    salvo = campanhas.salvar_campanha("REATIVACAO", "Oi {contato}, a {empresa} tem condição especial este mês.", True, "gestor")
    assert salvo["status"] == "APROVADA" and salvo["aprovada_por"] == "gestor"
    campanhas.marcar_enviado("REATIVACAO", "inativo", "gestor")
    campanhas.registrar_consentimento("inativo", "AUTORIZADO", "WhatsApp", "gestor")
    item = campanhas.publico_detalhado("REATIVACAO")["clientes"][0]
    assert item["enviado_em"] and item["autorizacao"] == "AUTORIZADO"
    assert item["mensagem"] == "Oi Maria, a Laticinios Beta tem condição especial este mês."
    campanhas.registrar_consentimento("inativo", "RECUSADO", "WhatsApp", "gestor")
    assert campanhas.publico_detalhado("REATIVACAO")["clientes"][0]["link_whatsapp"] is None  # quem recusou não recebe


def test_posts_do_canal():
    posts = campanhas.posts_do_canal()
    assert len(posts) == 3 and all(p["texto"] for p in posts)
    assert "°C em baú de" in posts[1]["texto"]


def test_rotas_so_para_gestao(ambiente):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from core.admin_auth import UsuarioAutenticado, usuario_atual
    from routers.campanhas_comerciais_router import router

    app = FastAPI()
    app.include_router(router)

    def perfil(tipo, permissoes=None):
        return UsuarioAutenticado(id="u1", auth_id="u1", email="u1@example.invalid", nome="U", tipo_usuario=tipo, permissoes=permissoes or {})

    cliente = TestClient(app)
    try:
        app.dependency_overrides[usuario_atual] = lambda: perfil("VENDEDOR", {"oportunidades_editar": True})
        assert cliente.get("/crm-seguro/campanhas").status_code == 403
        app.dependency_overrides[usuario_atual] = lambda: perfil("ADMIN_MASTER")
        assert len(cliente.get("/crm-seguro/campanhas").json()["campanhas"]) == 5
        assert cliente.put("/crm-seguro/campanhas/REATIVACAO", json={"mensagem": "Oi {contato}, novidade para a {empresa}.", "aprovar": True}).status_code == 200
        csv = cliente.get("/crm-seguro/campanhas/reativacao/exportacao")
        assert csv.status_code == 200 and "Laticinios Beta" in csv.text
        assert cliente.post("/crm-seguro/campanhas/autorizacoes", json={"cliente_id": "../x", "status": "AUTORIZADO"}).status_code == 422
        assert cliente.get("/crm-seguro/campanhas/NAO_EXISTE").status_code == 404
    finally:
        app.dependency_overrides.pop(usuario_atual, None)


def test_recusa_nao_se_perde_com_mais_de_mil_autorizacoes(ambiente):
    from services import cofre_agente

    for i in range(1100):
        cofre_agente.gravar(cofre_agente.caminho("consentimentos", f"a{i:04d}.json"), {"status": "AUTORIZADO"})
    campanhas.registrar_consentimento("prospect-frota", "RECUSADO", "WhatsApp", "gestor")  # fica depois do milésimo na ordem
    assert len(campanhas.consentimentos()) == 1101
    gama = campanhas.publico_detalhado("CONQUISTA_CONCORRENTE")["clientes"][0]
    assert gama["autorizacao"] == "RECUSADO" and gama["link_whatsapp"] is None


def test_envios_e_edicao_nao_se_sobrescrevem(ambiente):
    campanhas.salvar_campanha("REATIVACAO", "Oi {contato}, novidade para a {empresa}.", True, "gestor")
    campanhas.marcar_enviado("REATIVACAO", "inativo", "a")
    campanhas.marcar_enviado("REATIVACAO", "outro", "b")
    campanhas.salvar_campanha("REATIVACAO", "Oi {contato}, condição nova para a {empresa}.", True, "gestor")
    assert set(campanhas.ler_campanha("REATIVACAO")["enviados"]) == {"inativo", "outro"}
