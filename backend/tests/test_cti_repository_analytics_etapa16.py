import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")

import pytest

from repositories import cti_repository
from repositories.cti_repository import CTIRepository
from services.base_analytics import consolidar_dashboard, filtrar_registros


class Resultado:
    def __init__(self, data=None):
        self.data = data or []


class FakeTabelaPaginada:
    def __init__(self, registros, chamadas, falhar_inicio=None):
        self.registros = registros
        self.chamadas = chamadas
        self.falhar_inicio = falhar_inicio
        self.inicio = 0
        self.fim = len(registros) - 1
        self.colunas = "*"

    def select(self, colunas, *_args, **_kwargs):
        self.colunas = colunas
        return self

    def range(self, inicio, fim):
        self.inicio = inicio
        self.fim = fim
        self.chamadas.append((inicio, fim))
        return self

    def execute(self):
        if self.falhar_inicio == self.inicio:
            raise Exception("timeout supabase pagina intermediaria")
        pagina = self.registros[self.inicio:self.fim + 1]
        if self.colunas != "*":
            campos = [campo.strip() for campo in self.colunas.split(",")]
            pagina = [
                {campo: registro.get(campo) for campo in campos}
                for registro in pagina
            ]
        return Resultado(pagina)


class FakeSupabasePaginado:
    def __init__(self, registros, falhar_inicio=None):
        self.registros = registros
        self.chamadas = []
        self.falhar_inicio = falhar_inicio

    def table(self, _nome):
        return FakeTabelaPaginada(
            self.registros,
            self.chamadas,
            self.falhar_inicio,
        )


def registro(indice, origem_base="BRASIL", autorizado=None, estado="SP"):
    return {
        "hash_registro": f"hash-{indice}",
        "cliente": f"Cliente {indice % 11}",
        "cidade": f"Cidade {indice % 7}",
        "estado": estado,
        "implementador": f"Implementadora {indice % 5}",
        "valor": 100,
        "origem_dado": origem_base,
        "origem_base": origem_base,
        "autorizado": autorizado,
        "aba_origem": "Viena SP 2026" if origem_base == "VIENA_SP" else "Brasil",
    }


def ler_quantidade(monkeypatch, quantidade):
    fake = FakeSupabasePaginado([registro(i) for i in range(quantidade)])
    monkeypatch.setattr(cti_repository, "supabase", fake)
    dados = CTIRepository().buscar_cti_anfir()
    return fake, dados


@pytest.mark.parametrize("quantidade", [10, 1000, 1001, 2427])
def test_leitura_integral_paginada(monkeypatch, quantidade):
    fake, dados = ler_quantidade(monkeypatch, quantidade)

    assert len(dados) == quantidade
    assert len({item["hash_registro"] for item in dados}) == quantidade
    assert fake.chamadas[0] == (0, 999)
    assert fake.chamadas[-1][0] <= quantidade


def test_paginacao_encerra_apos_pagina_vazia_quando_multiplo_exato(monkeypatch):
    fake, dados = ler_quantidade(monkeypatch, 1000)

    assert len(dados) == 1000
    assert fake.chamadas == [(0, 999), (1000, 1999)]


def test_paginacao_trata_erro_intermediario_de_forma_segura(monkeypatch):
    fake = FakeSupabasePaginado(
        [registro(i) for i in range(1500)],
        falhar_inicio=1000,
    )
    monkeypatch.setattr(cti_repository, "supabase", fake)

    with pytest.raises(RuntimeError, match="Erro seguro ao paginar"):
        CTIRepository().buscar_cti_anfir()


def test_contextos_brasil_viena_e_consolidado(monkeypatch):
    registros = [
        registro(1, "BRASIL", None, "SP"),
        registro(2, "BRASIL", None, "RJ"),
        registro(3, "VIENA_SP", "VIENA", "SP"),
    ]
    fake = FakeSupabasePaginado(registros)
    monkeypatch.setattr(cti_repository, "supabase", fake)

    dados = CTIRepository().buscar_cti_anfir()
    brasil = filtrar_registros(dados, "BRASIL")
    viena = filtrar_registros(dados, "VIENA_SP", "VIENA")

    assert len(dados) == 3
    assert len(brasil) == 2
    assert len(viena) == 1
    assert {item["origem_base"] for item in brasil} == {"BRASIL"}
    assert {item["autorizado"] for item in viena} == {"VIENA"}


def test_indicadores_consolidados_ticket_rankings_e_vazio():
    registros = [
        {"cliente": "Cliente A", "estado": "SP", "cidade": "Sao Paulo", "implementadora": "PAVAN", "valor": 100},
        {"cliente": "Cliente A", "estado": "SP", "cidade": "Campinas", "implementadora": "PAVAN", "valor": 200},
        {"cliente": "Cliente B", "estado": "RJ", "cidade": "Rio", "implementadora": "RANDON", "valor": 300},
    ]

    dashboard = consolidar_dashboard(registros)

    assert dashboard["fonte_indicadores"] == "cti_anfir_repository_paginado"
    assert dashboard["total_registros"] == 3
    assert dashboard["total_clientes"] == 2
    assert dashboard["total_estados"] == 2
    assert dashboard["total_municipios"] == 3
    assert dashboard["total_implementadoras"] == 2
    assert dashboard["faturamento_total"] == 600
    assert dashboard["ticket_medio"] == 200
    assert dashboard["ranking_implementadoras"][0] == {"nome": "PAVAN", "quantidade": 2}
    assert dashboard["ranking_clientes"][0] == {"nome": "Cliente A", "quantidade": 2}

    vazio = consolidar_dashboard([])
    assert vazio["total_registros"] == 0
    assert vazio["ticket_medio"] == 0
    assert vazio["ranking_clientes"] == []


def test_amostra_operacional_nao_carrega_base_inteira(monkeypatch):
    fake = FakeSupabasePaginado([registro(i) for i in range(2427)])
    monkeypatch.setattr(cti_repository, "supabase", fake)

    dados = CTIRepository().buscar_amostra_cti_anfir(10)

    assert len(dados) == 10
    assert fake.chamadas == [(0, 9)]
