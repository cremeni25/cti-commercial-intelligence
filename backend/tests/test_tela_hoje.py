"""Tela Hoje: junta prioridades, carteira e comissões em no máximo 5 cartões."""
import pytest

from services import indicacoes_comerciais as ind
from services import tela_hoje
from tests import cofre_falso
from tests.test_carteira_setorizada import base  # noqa: F401  (fixture)


def _prioridade(n, categoria="risco"):
    return {"titulo": f"Negócio {n} parado", "explicacao": "Sem contato há 20 dias", "acao_recomendada": "Ligar para o cliente",
            "cliente_nome": f"Cliente {n}", "valor": 1000 * n, "rota": f"/oportunidades/o{n}", "rota_app": f"/crm-app/oportunidades/o{n}", "categoria": categoria}


@pytest.fixture
def ambiente(base, monkeypatch):  # noqa: F811
    estado = {"prioridades": [_prioridade(i) for i in range(1, 7)]}
    monkeypatch.setattr("services.inteligencia_comercial.gerar_briefing",
                        lambda **k: {"manchete": "3 negócios pedem atenção.", "prioridades": estado["prioridades"]})
    cofre_falso.instalar(monkeypatch)
    ind._limpar_cache()
    yield estado
    ind._limpar_cache()


def test_vendedor_recebe_negocios_e_carteira(ambiente):
    r = tela_hoje.montar("ana", consolidado=False, master=False, pode_comercial=True)
    assert len(r["cartoes"]) == 5 and r["manchete"] == "3 negócios pedem atenção."
    assert [c["tipo"] for c in r["cartoes"]] == ["negocio"] * 5  # Ana não tem cliente a abordar na carteira
    assert r["cartoes"][0]["href"] == "/oportunidades/o1" and r["cartoes"][0]["acao"] == "Ligar para o cliente"
    beto = tela_hoje.montar("beto", consolidado=False, master=False, pode_comercial=True)
    assert [c["tipo"] for c in beto["cartoes"]] == ["negocio"] * 4 + ["carteira"]
    assert beto["cartoes"][-1]["titulo"] == "Reative este cliente: Laticinios Beta"
    assert beto["cartoes"][-1]["href"] == "/carteira?empresa=inativo"


def test_gestao_ve_renovacao_e_master_ve_comissao(ambiente):
    joao = ind.salvar_indicador({"nome": "João"}, "m")
    i = ind.registrar_indicacao({"indicador_id": joao["id"], "cliente_nome": "X", "regiao": "Y", "linha": "TRAILER", "quantidade": 2, "valor_final": 1}, "m")
    ind.atualizar_indicacao(i["id"], {"status": "VENDIDA"}, "m")
    ind.atualizar_indicacao(i["id"], {"comissao_status": "NF_RECEBIDA", "nota_fiscal": "1"}, "m")
    r = tela_hoje.montar("master", consolidado=True, master=True, pode_comercial=True)
    assert r["cartoes"][0]["titulo"] == "Pagar 1 comissão com nota fiscal: R$ 2.800"
    assert r["cartoes"][-1]["titulo"] == "Ofereça a renovação: Transportes Gama"
    assert len(r["cartoes"]) == 5


def test_falha_de_uma_fonte_nao_derruba_as_outras(ambiente, monkeypatch):
    def quebra(**k):
        raise RuntimeError("fora do ar")
    monkeypatch.setattr("services.inteligencia_comercial.gerar_briefing", quebra)
    r = tela_hoje.montar("master", consolidado=True, master=False, pode_comercial=True)
    assert [c["tipo"] for c in r["cartoes"]] == ["carteira"]
    assert r["limitacoes"] == ["Prioridades de negócios indisponíveis nesta leitura."]


def test_sem_perfil_comercial_nao_ve_nada(ambiente):
    r = tela_hoje.montar("x", consolidado=False, master=False, pode_comercial=False)
    assert r["cartoes"] == [] and r["manchete"] == "Tudo em dia por aqui."
