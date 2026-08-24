import importlib.util
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException


def _carregar_modulo(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    caminho = Path(__file__).resolve().parents[1] / "routers" / "crm_router.py"
    spec = importlib.util.spec_from_file_location("crm_router_resiliencia_test", caminho)
    modulo = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(modulo)
    monkeypatch.setattr(modulo.time, "sleep", lambda _: None)
    return modulo


class _Consulta:
    def __init__(self, falhas: int, dados=None):
        self.falhas = falhas
        self.dados = dados or []
        self.tentativas = 0

    def select(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        self.tentativas += 1
        if self.tentativas <= self.falhas:
            raise httpx.ReadError(
                "Resource temporarily unavailable",
                request=httpx.Request("GET", "https://example.supabase.co/rest/v1/cti_atividades"),
            )
        return SimpleNamespace(data=self.dados)


class _Supabase:
    def __init__(self, consulta):
        self.consulta = consulta

    def table(self, nome):
        assert nome == "cti_atividades"
        return self.consulta


def test_listar_atividades_recupera_readerror_transitorio(monkeypatch):
    modulo = _carregar_modulo(monkeypatch)
    consulta = _Consulta(falhas=1, dados=[{"id": "atividade-1"}])
    monkeypatch.setattr(modulo, "supabase", _Supabase(consulta))

    assert modulo.listar_atividades() == [{"id": "atividade-1"}]
    assert consulta.tentativas == 2


def test_listar_atividades_retorna_503_apos_tres_falhas(monkeypatch):
    modulo = _carregar_modulo(monkeypatch)
    consulta = _Consulta(falhas=3)
    monkeypatch.setattr(modulo, "supabase", _Supabase(consulta))

    with pytest.raises(HTTPException) as erro:
        modulo.listar_atividades()

    assert erro.value.status_code == 503
    assert consulta.tentativas == 3
    assert "temporariamente indisponível" in str(erro.value.detail)
