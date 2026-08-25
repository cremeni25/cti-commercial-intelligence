from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from routers.documentos_comerciais_listagem_router import _leitura_resiliente


class QueryFake:
    def __init__(self, executor):
        self._executor = executor

    def execute(self):
        return self._executor()


def test_leitura_resiliente_recupera_apos_read_error(monkeypatch):
    tentativas = {"n": 0}
    monkeypatch.setattr("routers.documentos_comerciais_listagem_router.time.sleep", lambda _: None)

    def executor():
        tentativas["n"] += 1
        if tentativas["n"] == 1:
            raise httpx.ReadError("transitório")
        return SimpleNamespace(data=[{"id": "ok"}])

    resultado = _leitura_resiliente(lambda: QueryFake(executor))

    assert resultado == [{"id": "ok"}]
    assert tentativas["n"] == 2


def test_leitura_resiliente_retorna_503_apos_esgotar_tentativas(monkeypatch):
    monkeypatch.setattr("routers.documentos_comerciais_listagem_router.time.sleep", lambda _: None)

    def executor():
        raise httpx.ReadError("persistente")

    with pytest.raises(HTTPException) as exc:
        _leitura_resiliente(lambda: QueryFake(executor), tentativas=3)

    assert exc.value.status_code == 503
    assert "temporariamente indisponível" in str(exc.value.detail)
