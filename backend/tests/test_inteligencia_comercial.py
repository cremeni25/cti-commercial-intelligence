"""Agente de Inteligência Comercial: regras, priorização, escopo e HTTP."""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core import application_access
from core.admin_auth import usuario_atual
from main import app
from services.inteligencia_comercial import (
    Sinal,
    filtrar_escopo,
    montar_briefing,
    registrar_provedor,
    remover_provedor,
)
from services.inteligencia_comercial import servico

HOJE = date(2026, 11, 7)


def _op(oid, **campos):
    base = {
        "oportunidade_id": oid, "titulo": f"Negócio {oid}", "cliente_id": f"cli-{oid}", "cliente_nome": f"Cliente {oid}",
        "responsavel_id": "vend-1", "etapa": "ATIVIDADE", "status_oportunidade": "ABERTA", "probabilidade": 40,
        "valor": 100000.0, "valor_ponderado": 40000.0, "linha_equipamento": "TRAILER", "equipamento": "X4 7500",
        "data_fechamento_prevista": "2026-12-15", "created_at": "2026-11-01T10:00:00+00:00", "updated_at": "2026-11-05T10:00:00+00:00",
        "encerrada": False,
    }
    base.update(campos)
    return base


def _at(aid, **campos):
    base = {"id": aid, "status": "PENDENTE", "data": "2026-11-20", "titulo": "Retorno", "usuario_id": "vend-1",
            "cliente_nome": "Cliente X", "created_at": "2026-11-05T10:00:00+00:00"}
    base.update(campos)
    return base


def _codigos(briefing):
    return briefing["sinais_por_codigo"]


def test_followup_atrasado_e_agenda_de_hoje():
    briefing = montar_briefing([], [_at("a1", data="2026-10-28"), _at("a2", data="2026-11-07"), _at("a3", data="2026-11-01", status="CONCLUIDA")], hoje=HOJE)
    assert _codigos(briefing) == {"FOLLOWUP_ATRASADO": 1, "AGENDA_HOJE": 1}
    atrasado = next(p for p in briefing["prioridades"] if p["codigo"] == "FOLLOWUP_ATRASADO")
    assert atrasado["dias"] == 10 and atrasado["severidade"] == "alta"
    assert briefing["indicadores"][1]["valor"] == 2


def test_negocio_saudavel_com_proximo_passo_nao_gera_alerta():
    briefing = montar_briefing([_op("o1")], [_at("a1", oportunidade_id="o1")], hoje=HOJE)
    assert briefing["total_sinais"] == 0
    assert briefing["manchete"].startswith("Carteira em dia")


def test_sem_proximo_passo_parado_e_previsao_vencida():
    op = _op("o1", data_fechamento_prevista="2026-10-01", updated_at="2026-09-01T00:00:00+00:00", created_at="2026-08-01T00:00:00+00:00")
    briefing = montar_briefing([op], [], hoje=HOJE)
    assert {"FECHAMENTO_VENCIDO", "OPORTUNIDADE_PARADA", "SEM_PROXIMO_PASSO"} <= set(_codigos(briefing))
    # Uma prioridade por negócio; os demais sinais ficam relacionados.
    assert len(briefing["prioridades"]) == 1
    assert len(briefing["prioridades"][0]["sinais_relacionados"]) == 2
    assert briefing["indicadores"][2]["valor"] == 100000.0  # valor em risco contado uma vez


def test_proposta_sem_retorno_tem_precedencia_sobre_parada():
    op = _op("o1", etapa="PROPOSTA", status_proposta="ENVIADA", proposta_numero="P-12", updated_at="2026-10-20T00:00:00+00:00", created_at="2026-10-01T00:00:00+00:00")
    agendada_antes = _at("a1", oportunidade_id="o1", created_at="2026-10-20T00:00:00+00:00")
    briefing = montar_briefing([op], [agendada_antes], hoje=HOJE)
    assert "PROPOSTA_SEM_RETORNO" in _codigos(briefing)
    assert "OPORTUNIDADE_PARADA" not in _codigos(briefing)
    assert "P-12" in briefing["prioridades"][0]["explicacao"]


def test_pronto_para_fechar():
    op = _op("o1", probabilidade=80, data_fechamento_prevista="2026-11-20")
    briefing = montar_briefing([op], [_at("a1", oportunidade_id="o1")], hoje=HOJE)
    assert _codigos(briefing) == {"PRONTO_PARA_FECHAR": 1}
    assert briefing["prioridades"][0]["categoria"] == "oportunidade"


@pytest.mark.parametrize("etapa", ["GANHO", "PERDIDO", "CANCELADO", "FATURADO", "ENCERRADO"])
def test_negocio_encerrado_nunca_recebe_recomendacao(etapa):
    op = _op("o1", etapa=etapa, encerrada=True, data_fechamento_prevista="2026-01-01", updated_at="2025-01-01T00:00:00+00:00")
    briefing = montar_briefing([op], [], hoje=HOJE)
    assert briefing["total_sinais"] == 0
    assert briefing["pipeline"]["quantidade_aberta"] == 0


def test_pedido_sem_movimento_vai_para_pos_venda():
    op = _op("o1", etapa="PEDIDO", pedido_id="ped-9", pedido_numero="PD-9", updated_at="2026-10-10T00:00:00+00:00", created_at="2026-10-01T00:00:00+00:00")
    briefing = montar_briefing([op], [], hoje=HOJE)
    assert _codigos(briefing) == {"PEDIDO_SEM_MOVIMENTO": 1}
    assert briefing["prioridades"][0]["rota"] == "/pedidos/ped-9"
    assert briefing["qualidade"]["negocios_avaliados"] == 0  # pós-venda não entra na qualidade de pipeline


def test_qualidade_e_pipeline():
    ops = [
        _op("o1"),
        _op("o2", valor=0, valor_ponderado=0, data_fechamento_prevista=None, linha_equipamento=None, equipamento=None, etapa="PROPOSTA"),
    ]
    briefing = montar_briefing(ops, [_at("a1", oportunidade_id="o1"), _at("a2", oportunidade_id="o2")], hoje=HOJE)
    codigos = {p["codigo"] for p in briefing["qualidade"]["problemas"]}
    assert codigos == {"SEM_VALOR", "SEM_PREVISAO", "SEM_EQUIPAMENTO"}
    assert briefing["qualidade"]["indice"] == round(100 * (1 - 3 / 8))
    etapas = {e["etapa"]: e for e in briefing["pipeline"]["etapas"]}
    assert etapas["ATIVIDADE"]["quantidade"] == 1 and etapas["PROPOSTA"]["quantidade"] == 1
    assert briefing["pipeline"]["valor_aberto"] == 100000.0


def test_ganhos_do_mes():
    ops = [_op("o1", etapa="GANHO", encerrada=True, data_fechamento_real="2026-11-03", valor=50000.0), _op("o2", etapa="GANHO", encerrada=True, data_fechamento_real="2026-10-03")]
    briefing = montar_briefing(ops, [], hoje=HOJE)
    ganhos = next(i for i in briefing["indicadores"] if i["codigo"] == "GANHOS_MES")
    assert ganhos["valor"] == 50000.0


def test_prioridade_considera_gravidade_valor_e_tempo():
    pequeno = _op("o1", valor=1000.0, data_fechamento_prevista="2026-11-01")
    grande = _op("o2", valor=900000.0, data_fechamento_prevista="2026-11-01")
    briefing = montar_briefing([pequeno, grande], [_at("a1", oportunidade_id="o1"), _at("a2", oportunidade_id="o2")], hoje=HOJE)
    assert [p["entidade_id"] for p in briefing["prioridades"]] == ["o2", "o1"]


def test_modulo_novo_contribui_sinais_e_falha_isolada():
    @registrar_provedor("teste_treinamento", modulo="treinamentos")
    def _provedor(contexto):
        return [Sinal(codigo="TREINAMENTO_RECOMENDADO", categoria="acao", severidade="baixa", titulo="Trilha Vector",
                      explicacao="3 propostas de TR perdidas por objeção técnica.", acao_recomendada="Concluir a trilha TR.",
                      entidade_tipo="treinamento", entidade_id="tr-1")]

    @registrar_provedor("teste_quebrado", modulo="quebrado")
    def _quebrado(contexto):
        raise RuntimeError("falha simulada")

    try:
        briefing = montar_briefing([], [], hoje=HOJE)
    finally:
        remover_provedor("teste_treinamento")
        remover_provedor("teste_quebrado")
    assert briefing["sinais_por_codigo"] == {"TREINAMENTO_RECOMENDADO": 1}
    situacao = {p["codigo"]: p for p in briefing["provedores"]}
    assert situacao["teste_quebrado"]["ok"] is False
    assert briefing["limitacoes"]


def test_sinal_rejeita_categoria_invalida():
    with pytest.raises(ValueError):
        Sinal(codigo="X", categoria="outra", severidade="alta", titulo="", explicacao="", acao_recomendada="", entidade_tipo="", entidade_id="")


def test_filtrar_escopo_mantem_somente_carteira_do_responsavel():
    ops = [_op("o1", responsavel_id="vend-1"), _op("o2", responsavel_id="vend-2")]
    ats = [_at("a1", usuario_id="vend-2", oportunidade_id="o1"), _at("a2", usuario_id="vend-2", oportunidade_id="o2"), _at("a3", usuario_id="vend-1")]
    proprias, atividades = filtrar_escopo(ops, ats, "vend-1")
    assert [o["oportunidade_id"] for o in proprias] == ["o1"]
    assert {a["id"] for a in atividades} == {"a1", "a3"}


@pytest.fixture
def cliente_http(monkeypatch):
    estado = {"perfil": SimpleNamespace(id="vend-1", tipo_usuario="REPRES_REGIAO_01", permissoes={"oportunidades_visualizar": True})}
    monkeypatch.setattr(application_access, "usuario_atual", lambda *_: estado["perfil"])
    monkeypatch.setattr(servico, "_carregar_oportunidades", lambda: [_op("o1", responsavel_id="vend-1"), _op("o2", responsavel_id="vend-2", data_fechamento_prevista="2026-10-01")])
    monkeypatch.setattr(servico, "_carregar_atividades", lambda: [_at("a1", oportunidade_id="o1")])
    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[usuario_atual] = lambda: estado["perfil"]
    try:
        with TestClient(app) as client:
            yield client, estado
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)


def test_http_vendedor_recebe_somente_a_propria_carteira(cliente_http):
    client, _ = cliente_http
    resposta = client.get("/crm-seguro/inteligencia/briefing")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["escopo"] == {"tipo": "individual", "responsavel_id": "vend-1"}
    assert corpo["pipeline"]["quantidade_aberta"] == 1
    assert client.get("/crm-seguro/inteligencia/briefing", params={"responsavel_id": "vend-2"}).status_code == 403


def test_http_master_ve_equipe_e_filtra_responsavel(cliente_http):
    client, estado = cliente_http
    estado["perfil"] = SimpleNamespace(id="master", tipo_usuario="ADMIN_MASTER", permissoes={})
    consolidado = client.get("/crm-seguro/inteligencia/briefing").json()
    assert consolidado["escopo"]["tipo"] == "consolidado"
    assert consolidado["pipeline"]["quantidade_aberta"] == 2
    filtrado = client.get("/crm-seguro/inteligencia/briefing", params={"responsavel_id": "vend-2"}).json()
    assert filtrado["escopo"] == {"tipo": "individual", "responsavel_id": "vend-2"}
    assert "FECHAMENTO_VENCIDO" in filtrado["sinais_por_codigo"]


def test_http_modulos_respeitam_permissoes(cliente_http):
    client, estado = cliente_http
    vendedor = {m["codigo"] for m in client.get("/crm-seguro/plataforma/modulos").json()["modulos"]}
    assert {"central", "oportunidades", "treinamentos"} <= vendedor
    assert "catalogo-produtos" not in vendedor and "pedidos" not in vendedor
    estado["perfil"] = SimpleNamespace(id="master", tipo_usuario="ADMIN_MASTER", permissoes={})
    corpo = client.get("/crm-seguro/plataforma/modulos").json()
    assert "catalogo-produtos" in {m["codigo"] for m in corpo["modulos"]}
    assert {p["codigo"] for p in corpo["provedores_inteligencia"]} >= {"agenda", "pipeline", "pedidos"}


def test_ia_conversacional_recebe_prioridades_como_fonte(monkeypatch):
    from services import ia_comercial_fonte_prioridades as fonte
    from services import ia_comercial_universo as universo

    fonte._CACHE.clear()
    monkeypatch.setattr(fonte, "_ORIGINAL_CARREGAR_FONTES", lambda usuario_id, tipo_usuario: ({"oportunidades": []}, {}))
    monkeypatch.setattr(servico, "_carregar_oportunidades", lambda: [_op("o1", responsavel_id="vend-1", data_fechamento_prevista="2026-10-01"), _op("o2", responsavel_id="vend-2", data_fechamento_prevista="2026-10-01")])
    monkeypatch.setattr(servico, "_carregar_atividades", lambda: [])
    fontes, metadados = fonte._carregar_fontes_com_prioridades("vend-1", "REPRES_REGIAO_01")
    assert {r["entidade_id"] for r in fontes["prioridades_comerciais"]} == {"o1"}
    assert metadados["prioridades_comerciais"]["erro"] is None
    assert "prioridades_comerciais" in universo.FONTES_PUBLICAS

    fonte._CACHE.clear()
    monkeypatch.setattr(servico, "_carregar_oportunidades", lambda: (_ for _ in ()).throw(RuntimeError("banco fora")))
    fontes, metadados = fonte._carregar_fontes_com_prioridades("vend-1", "REPRES_REGIAO_01")
    assert fontes["prioridades_comerciais"] == [] and metadados["prioridades_comerciais"]["erro"] == "RuntimeError"
    assert fontes["oportunidades"] == []
