from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routers import crm_scope_negocio_historico_router as modulo


def usuario(tipo="REPRES_REGIAO_01", identificador="user-1", acesso_total=False):
    return SimpleNamespace(
        id=identificador,
        tipo_usuario=tipo,
        permissoes={"acesso_total": acesso_total},
    )


def dados_criacao(responsavel="user-2"):
    return modulo.ClienteOportunidadeCreate(
        cliente=modulo.ClienteOportunidadeCreate.model_fields["cliente"].annotation(
            id="cliente-1", nome="Cliente Teste", cidade="São Paulo", estado="SP"
        ),
        oportunidade=modulo.ClienteOportunidadeCreate.model_fields["oportunidade"].annotation(
            responsavel_id=responsavel,
            titulo="Cotação de equipamentos",
            valor_estimado=1000,
            probabilidade=50,
        ),
    )


def test_criacao_regional_forca_responsavel_autenticado(monkeypatch):
    capturado = {}
    monkeypatch.setattr(modulo, "criar_cliente_e_oportunidade", lambda dados: capturado.setdefault("dados", dados) or {})
    modulo.criar_cliente_oportunidade_segura(dados_criacao(), usuario())
    assert capturado["dados"].oportunidade.responsavel_id == "user-1"


def test_master_preserva_responsavel_informado(monkeypatch):
    capturado = {}
    monkeypatch.setattr(modulo, "criar_cliente_e_oportunidade", lambda dados: capturado.setdefault("dados", dados) or {})
    modulo.criar_cliente_oportunidade_segura(dados_criacao("user-2"), usuario("ADMIN_MASTER"))
    assert capturado["dados"].oportunidade.responsavel_id == "user-2"


def test_timeline_regional_bloqueia_oportunidade_alheia(monkeypatch):
    monkeypatch.setattr(modulo, "obter_oportunidade", lambda _: {"id": "opp-2", "responsavel_id": "user-2"})
    with pytest.raises(HTTPException) as erro:
        modulo.timeline_oportunidade_segura("opp-2", usuario())
    assert erro.value.status_code == 404


def test_timeline_regional_libera_propria(monkeypatch):
    monkeypatch.setattr(modulo, "obter_oportunidade", lambda _: {"id": "opp-1", "responsavel_id": "user-1"})
    monkeypatch.setattr(modulo, "timeline_oportunidade", lambda _: {"oportunidade": {"id": "opp-1"}, "eventos": []})
    retorno = modulo.timeline_oportunidade_segura("opp-1", usuario())
    assert retorno["oportunidade"]["id"] == "opp-1"
