import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")

import pytest

from repositories import cti_repository
from repositories.cti_repository import (
    CTIRepository,
    _adaptar_dominio_para_persistencia,
    _adaptar_persistencia_para_dominio,
)


class Resultado:
    def __init__(self, data=None):
        self.data = data or []


class FakeTable:
    def __init__(self, db, erro=None):
        self.db = db
        self.erro = erro
        self.operacao = None
        self.payload = None
        self.hash = None

    def select(self, *_args, **_kwargs):
        self.operacao = "select"
        return self

    def eq(self, campo, valor):
        if campo == "hash_registro":
            self.hash = valor
        return self

    def limit(self, *_args):
        return self

    def insert(self, payload):
        self.operacao = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operacao = "update"
        self.payload = payload
        return self

    def execute(self):
        if self.erro:
            raise self.erro
        if self.operacao == "select":
            item = self.db.get(self.hash)
            return Resultado([item] if item else [])
        if self.operacao == "insert":
            self.db[self.payload["hash_registro"]] = dict(self.payload)
            return Resultado([self.payload])
        if self.operacao == "update":
            self.db[self.hash].update(self.payload)
            return Resultado([self.db[self.hash]])
        return Resultado([])


class FakeSupabase:
    def __init__(self, db=None, erro=None):
        self.db = db if db is not None else {}
        self.erro = erro

    def table(self, _nome):
        return FakeTable(self.db, self.erro)


def registro(hash_registro="abc", valor=100):
    return {
        "hash_registro": hash_registro,
        "implementadora": "RANDON",
        "origem_base": "BRASIL",
        "aba_origem": "Brasil",
        "valor": valor,
        "modelo_carrier": "NAO_PERSISTE",
    }


def test_insert_update_duplicado_e_adaptacao(monkeypatch):
    fake = FakeSupabase()
    monkeypatch.setattr(cti_repository, "supabase", fake)
    repo = CTIRepository()

    assert _adaptar_dominio_para_persistencia(registro())["implementador"] == "RANDON"

    primeiro = repo.persistir_registros_idempotente([registro()])
    assert primeiro["inseridos"] == 1
    assert fake.db["abc"]["implementador"] == "RANDON"
    assert "implementadora" not in fake.db["abc"]
    assert "modelo_carrier" not in fake.db["abc"]

    duplicado = repo.persistir_registros_idempotente([registro()])
    assert duplicado["duplicados_ignorados"] == 1

    atualizado = repo.persistir_registros_idempotente([registro(valor=200)])
    assert atualizado["atualizados"] == 1
    assert fake.db["abc"]["valor"] == 200

    dominio = _adaptar_persistencia_para_dominio(fake.db["abc"])
    assert dominio["implementadora"] == "RANDON"
    assert dominio["origem_base"] == "BRASIL"


def test_erros_classificados(monkeypatch):
    monkeypatch.setattr(cti_repository, "supabase", FakeSupabase(erro=Exception("column origem_base does not exist")))
    repo = CTIRepository()
    resultado = repo.persistir_registros_idempotente([registro()])
    assert resultado["erros"] == 1
    assert resultado["erros_por_tipo"]["schema_incompativel"] == 1
    assert resultado["amostra_erros"][0]["etapa"] == "persistencia"

    monkeypatch.setattr(cti_repository, "supabase", FakeSupabase(erro=Exception("JWT auth failed")))
    resultado = repo.persistir_registros_idempotente([registro("auth")])
    assert resultado["erros_por_tipo"]["erro_autenticacao"] == 1

    monkeypatch.setattr(cti_repository, "supabase", FakeSupabase(erro=Exception("network timeout")))
    resultado = repo.persistir_registros_idempotente([registro("net")])
    assert resultado["erros_por_tipo"]["erro_rede"] == 1

    resultado = repo.persistir_registros_idempotente([registro(hash_registro=None)])
    assert resultado["erros_por_tipo"]["registro_sem_identificador"] == 1

class FakePagedTable:
    def __init__(self, registros):
        self.registros = registros
        self.inicio = 0
        self.fim = 0
        self.ranges = []

    def select(self, *_args, **_kwargs):
        return self

    def range(self, inicio, fim):
        self.inicio = inicio
        self.fim = fim
        self.ranges.append((inicio, fim))
        return self

    def execute(self):
        return Resultado(self.registros[self.inicio:self.fim + 1])


class FakePagedSupabase:
    def __init__(self, registros):
        self.tabela = FakePagedTable(registros)

    def table(self, _nome):
        return self.tabela


def test_buscar_cti_anfir_pagina_todos_os_registros(monkeypatch):
    registros = [
        {"hash_registro": str(i), "cliente": f"Cliente {i}", "implementador": "RANDON"}
        for i in range(5)
    ]
    fake = FakePagedSupabase(registros)
    monkeypatch.setattr(cti_repository, "supabase", fake)

    resultado = CTIRepository().buscar_cti_anfir(page_size=2)

    assert [item["hash_registro"] for item in resultado] == ["0", "1", "2", "3", "4"]
    assert fake.tabela.ranges == [(0, 1), (2, 3), (4, 5)]
    assert all(item["implementadora"] == "RANDON" for item in resultado)
