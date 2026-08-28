from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routers import crm_scope_atividades_router as modulo


def usuario(tipo="REPRES_REGIAO_01", identificador="user-1", acesso_total=False):
    return SimpleNamespace(
        id=identificador,
        tipo_usuario=tipo,
        permissoes={"acesso_total": acesso_total},
    )


def test_agenda_regional_retorna_somente_proprias():
    payload = {
        "itens": [
            {"id": "a1", "usuario_id": "user-1", "situacao": "HOJE"},
            {"id": "a2", "usuario_id": "user-2", "situacao": "ATRASADA"},
        ],
        "resumo": {},
    }
    resultado = modulo._filtrar_agenda(payload, usuario())
    assert [item["id"] for item in resultado["itens"]] == ["a1"]
    assert resultado["resumo"]["total"] == 1
    assert resultado["resumo"]["hoje"] == 1
    assert resultado["resumo"]["atrasadas"] == 0


def test_agenda_master_preserva_visao_consolidada():
    payload = {"itens": [{"id": "a1"}, {"id": "a2"}], "resumo": {"total": 2}}
    assert modulo._filtrar_agenda(payload, usuario("ADMIN_MASTER")) == payload


def test_criacao_regional_forca_usuario_autenticado(monkeypatch):
    capturado = {}
    monkeypatch.setattr(modulo, "obter_oportunidade", lambda _: {"responsavel_id": "user-1"})
    monkeypatch.setattr(modulo, "criar_atividade_operacional", lambda dados: capturado.setdefault("dados", dados) or [])
    atividade = modulo.AtividadeCreate(
        cliente_id="cliente-1",
        usuario_id="user-2",
        tipo="FOLLOW_UP",
        oportunidade_id="opp-1",
    )
    modulo.criar_atividade_segura(atividade, usuario())
    assert capturado["dados"].usuario_id == "user-1"


def test_criacao_regional_bloqueia_negociacao_de_outro_usuario(monkeypatch):
    monkeypatch.setattr(modulo, "obter_oportunidade", lambda _: {"responsavel_id": "user-2"})
    atividade = modulo.AtividadeCreate(
        cliente_id="cliente-1",
        usuario_id="user-1",
        tipo="FOLLOW_UP",
        oportunidade_id="opp-2",
    )
    with pytest.raises(HTTPException) as erro:
        modulo.criar_atividade_segura(atividade, usuario())
    assert erro.value.status_code == 404


def test_edicao_regional_bloqueia_atividade_de_outro_usuario(monkeypatch):
    monkeypatch.setattr(modulo, "obter_atividade", lambda _: {"id": "a2", "usuario_id": "user-2"})
    with pytest.raises(HTTPException) as erro:
        modulo.atualizar_atividade_segura("a2", modulo.AtividadeUpdate(titulo="x"), usuario())
    assert erro.value.status_code == 404
