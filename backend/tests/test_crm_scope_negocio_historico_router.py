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


def test_timeline_master_preserva_visao_consolidada(monkeypatch):
    monkeypatch.setattr(modulo, "obter_oportunidade", lambda _: {"id": "opp-2", "responsavel_id": "user-2"})
    monkeypatch.setattr(modulo, "timeline_oportunidade", lambda _: {"oportunidade": {"id": "opp-2"}, "eventos": []})
    retorno = modulo.timeline_oportunidade_segura("opp-2", usuario("ADMIN_MASTER"))
    assert retorno["oportunidade"]["id"] == "opp-2"
