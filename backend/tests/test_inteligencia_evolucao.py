"""Ajustes de sinais (não se aplica/adiar), aprendizado e vitrine do catálogo."""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core import application_access
from core.admin_auth import usuario_atual
from main import app
from routers import inteligencia_comercial_router as rota
from services import catalogo_vitrine as vitrine
from services.inteligencia_comercial import montar_briefing, servico
from services.inteligencia_comercial import feedback as fb

HOJE = date(2026, 11, 7)


def _op(oid, responsavel="vend-1", **extra):
    base = {"oportunidade_id": oid, "cliente_id": f"cli-{oid}", "cliente_nome": f"Cliente {oid}", "responsavel_id": responsavel,
            "etapa": "ATIVIDADE", "valor": 100000.0, "probabilidade": 40, "data_fechamento_prevista": "2026-10-01",
            "created_at": "2026-11-01T00:00:00+00:00", "updated_at": "2026-11-05T00:00:00+00:00", "linha_equipamento": "TRAILER"}
    base.update(extra)
    return base


def test_sinal_carrega_cliente_para_agendar_proximo_passo():
    briefing = montar_briefing([_op("o1")], [], hoje=HOJE)
    assert briefing["prioridades"][0]["cliente_id"] == "cli-o1"


def test_supressao_esconde_somente_o_sinal_ajustado():
    briefing = montar_briefing([_op("o1")], [], hoje=HOJE, supressoes={("FECHAMENTO_VENCIDO", "oportunidade", "o1")})
    assert "FECHAMENTO_VENCIDO" not in briefing["sinais_por_codigo"]
    assert briefing["sinais_por_codigo"].get("SEM_PROXIMO_PASSO") == 1
    assert briefing["sinais_suprimidos"] == 1


def test_supressao_expira_e_prazos_sao_limitados():
    registros = [{"codigo": "A", "entidade_tipo": "oportunidade", "entidade_id": "1", "suprimir_ate": "2026-11-06"},
                 {"codigo": "B", "entidade_tipo": "oportunidade", "entidade_id": "1", "suprimir_ate": "2026-11-07"}]
    assert fb.supressoes_ativas(registros, HOJE) == {("B", "oportunidade", "1")}
    assert fb.prazo_supressao("ADIAR", HOJE, date(2027, 6, 1)) == date(2027, 1, 6)
    assert fb.prazo_supressao("ADIAR", HOJE, None) == date(2026, 11, 14)
    assert fb.prazo_supressao("NAO_SE_APLICA", HOJE, None) == date(2026, 12, 7)


def test_resumo_aprendizado_ordena_alertas_mais_dispensados():
    resumo = fb.resumo_aprendizado([
        {"codigo": "OPORTUNIDADE_PARADA", "motivo": "ALERTA_CEDO_DEMAIS"},
        {"codigo": "OPORTUNIDADE_PARADA", "motivo": "ALERTA_CEDO_DEMAIS"},
        {"codigo": "SEM_PROXIMO_PASSO", "motivo": "JA_TRATADO"},
    ])
    assert resumo["sinais"][0]["codigo"] == "OPORTUNIDADE_PARADA"
    assert resumo["sinais"][0]["motivos"][0]["rotulo"] == "Alerta cedo demais para este tipo de venda"


@pytest.fixture
def http(monkeypatch):
    estado = {"perfil": SimpleNamespace(id="vend-1", tipo_usuario="REPRES_REGIAO_01", permissoes={"oportunidades_visualizar": True}), "gravados": [], "falhar": False}
    monkeypatch.setattr(application_access, "usuario_atual", lambda *_: estado["perfil"])
    monkeypatch.setattr(servico, "_carregar_oportunidades", lambda: [_op("o1"), _op("o2", responsavel="vend-2")])
    monkeypatch.setattr(servico, "_carregar_atividades", lambda: [])
    monkeypatch.setattr(servico, "_carregar_feedback", lambda hoje: list(estado["gravados"]))
    monkeypatch.setattr(rota, "hoje_operacional", lambda: HOJE)

    def gravar(**dados):
        if estado["falhar"]:
            raise fb.FeedbackIndisponivel("relation does not exist")
        registro = {**dados, "suprimir_ate": fb.prazo_supressao(dados["decisao"], dados["hoje"], dados["adiar_ate"]).isoformat()}
        estado["gravados"].append(registro)
        return registro

    monkeypatch.setattr(rota, "registrar_feedback", gravar)
    monkeypatch.setattr(rota, "carregar_feedback", lambda desde=None: [{"codigo": "OPORTUNIDADE_PARADA", "motivo": "JA_TRATADO"}])
    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[usuario_atual] = lambda: estado["perfil"]
    try:
        with TestClient(app) as client:
            yield client, estado
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)


def test_http_adiar_sinal_some_da_leitura_ate_o_prazo(http):
    client, estado = http
    corpo = {"codigo": "FECHAMENTO_VENCIDO", "entidade_tipo": "oportunidade", "entidade_id": "o1", "decisao": "ADIAR", "motivo": "CLIENTE_PEDIU_AGUARDAR", "adiar_ate": "2026-11-20"}
    resposta = client.post("/crm-seguro/inteligencia/feedback", json=corpo)
    assert resposta.status_code == 201 and resposta.json()["suprimir_ate"] == "2026-11-20"
    assert estado["gravados"][0]["usuario_id"] == "vend-1"
    briefing = client.get("/crm-seguro/inteligencia/briefing").json()
    assert "FECHAMENTO_VENCIDO" not in briefing["sinais_por_codigo"]
    assert briefing["sinais_suprimidos"] == 1


def test_http_nao_ajusta_sinal_de_outra_carteira_nem_motivo_invalido(http):
    client, estado = http
    alheio = {"codigo": "FECHAMENTO_VENCIDO", "entidade_tipo": "oportunidade", "entidade_id": "o2", "decisao": "NAO_SE_APLICA", "motivo": "JA_TRATADO"}
    assert client.post("/crm-seguro/inteligencia/feedback", json=alheio).status_code == 404
    assert client.post("/crm-seguro/inteligencia/feedback", json={**alheio, "entidade_id": "o1", "motivo": "XYZ"}).status_code == 422
    assert client.post("/crm-seguro/inteligencia/feedback", json={**alheio, "entidade_id": "o1", "decisao": "ADIAR", "adiar_ate": "2026-11-07"}).status_code == 422
    assert estado["gravados"] == []


def test_http_tabela_ausente_responde_503_claro(http):
    client, estado = http
    estado["falhar"] = True
    resposta = client.post("/crm-seguro/inteligencia/feedback", json={"codigo": "SEM_PROXIMO_PASSO", "entidade_tipo": "oportunidade", "entidade_id": "o1", "decisao": "NAO_SE_APLICA", "motivo": "JA_TRATADO"})
    assert resposta.status_code == 503 and "ativado" in resposta.json()["detail"]


def test_http_aprendizado_somente_gestao(http):
    client, estado = http
    assert client.get("/crm-seguro/inteligencia/aprendizado").status_code == 403
    estado["perfil"] = SimpleNamespace(id="master", tipo_usuario="ADMIN_MASTER", permissoes={})
    assert client.get("/crm-seguro/inteligencia/aprendizado").json()["total_ajustes"] == 1


EQUIPAMENTOS = [
    {"codigo": "VECTOR-8500", "linha_produto": "TRAILER", "modelo_base": "VECTOR 8500", "nome_comercial": "VECTOR 8500", "configuracao": "PADRAO", "ordem": 20, "descricao_tecnica": {"capacidade": "Alta", "vazio": ""}},
    {"codigo": "SUPRA-850", "linha_produto": "DIESEL TRUCK", "modelo_base": "SUPRA 850", "nome_comercial": "SUPRA 850", "compressor": "05K 4CC", "possui_eletrico": True, "ordem": 120},
]
PRECOS = [
    {"equipamento_codigo": "VECTOR-8500", "preco_cheio": 100, "vigencia_inicio": "2026-01-01", "tabela_codigo": "T1"},
    {"equipamento_codigo": "VECTOR-8500", "preco_cheio": 120, "vigencia_inicio": "2026-08-01", "tabela_codigo": "T2"},
    {"equipamento_codigo": "VECTOR-8500", "preco_cheio": 999, "vigencia_inicio": "2027-01-01", "tabela_codigo": "FUTURA"},
]
MATERIAIS = {"linktree_url": "https://linktr.ee/exemplo", "materiais": [
    {"titulo": "Catálogo geral", "url": "https://exemplo.com/geral.pdf", "tipo": "catalogo"},
    {"titulo": "Linha Trailer", "url": "https://exemplo.com/tr.pdf", "linhas": ["TR"]},
    {"titulo": "Ficha Supra", "url": "https://exemplo.com/supra.pdf", "tipo": "ficha_tecnica", "termos": ["supra 850"]},
    {"titulo": "Inseguro", "url": "http://exemplo.com/x.pdf"},
]}


def test_vitrine_cruza_precos_vigentes_e_materiais():
    resultado = vitrine.montar_vitrine(equipamentos=EQUIPAMENTOS, precos=PRECOS, materiais_conteudo=MATERIAIS, ver_precos=True, hoje=HOJE, fonte="catalogo_comercial")
    linhas = {l["codigo"]: l for l in resultado["linhas"]}
    vector = linhas["TRAILER"]["equipamentos"][0]
    assert vector["preco_vigente"]["valor"] == 120.0 and vector["preco_vigente"]["tabela"] == "T2"
    assert vector["descricao_tecnica"] == {"capacidade": "Alta"}
    assert [m["titulo"] for m in linhas["TRAILER"]["materiais"]] == ["Linha Trailer"]
    assert [m["titulo"] for m in linhas["DIESEL TRUCK"]["equipamentos"][0]["materiais"]] == ["Ficha Supra"]
    assert [m["titulo"] for m in resultado["materiais_gerais"]] == ["Catálogo geral"]
    assert resultado["linktree_url"] == "https://linktr.ee/exemplo" and resultado["total_equipamentos"] == 2


def test_vitrine_oculta_preco_sem_permissao():
    resultado = vitrine.montar_vitrine(equipamentos=EQUIPAMENTOS, precos=PRECOS, materiais_conteudo={}, ver_precos=False, hoje=HOJE, fonte="catalogo_comercial")
    assert all(e["preco_vigente"] is None for l in resultado["linhas"] for e in l["equipamentos"])


def test_vitrine_cai_para_catalogo_oficial_sem_precos(monkeypatch):
    monkeypatch.setattr(vitrine, "_ler_catalogo_comercial", lambda: (_ for _ in ()).throw(RuntimeError("fora")))
    resultado = vitrine.carregar_vitrine(ver_precos=True, hoje=HOJE)
    assert resultado["fonte"] == "catalogo_oficial_sem_precos" and resultado["precos_visiveis"] is False
    assert resultado["total_equipamentos"] > 0


def test_http_vitrine_respeita_permissoes(http, monkeypatch):
    client, estado = http
    monkeypatch.setattr(vitrine, "_ler_catalogo_comercial", lambda: (EQUIPAMENTOS, PRECOS))
    corpo = client.get("/crm-seguro/catalogo/vitrine").json()
    assert corpo["precos_visiveis"] is False
    estado["perfil"] = SimpleNamespace(id="v2", tipo_usuario="REPRES_REGIAO_01", permissoes={"propostas_emitir": True})
    assert client.get("/crm-seguro/catalogo/vitrine").json()["precos_visiveis"] is True
    estado["perfil"] = SimpleNamespace(id="v3", tipo_usuario="REPRES_REGIAO_01", permissoes={})
    assert client.get("/crm-seguro/catalogo/vitrine").status_code == 403


def test_arquivo_de_materiais_versionado_e_valido():
    conteudo = vitrine._materiais_brutos()
    assert isinstance(conteudo.get("materiais"), list)
    assert len(vitrine.materiais_validos(conteudo)) == len(conteudo["materiais"]), "todo material do arquivo deve ter título e https"


def test_material_de_modelo_sem_cadastro_aparece_na_linha():
    conteudo = {"materiais": [
        {"titulo": "Vector 8700", "url": "https://exemplo.com/v8700.pdf", "linhas": ["TR"], "termos": ["vector 8700"]},
        {"titulo": "Vector 8500", "url": "https://exemplo.com/v8500.pdf", "linhas": ["TR"], "termos": ["vector 8500"]},
    ]}
    resultado = vitrine.montar_vitrine(equipamentos=EQUIPAMENTOS, precos=[], materiais_conteudo=conteudo, ver_precos=False, hoje=HOJE, fonte="catalogo_comercial")
    trailer = next(l for l in resultado["linhas"] if l["codigo"] == "TRAILER")
    assert [m["titulo"] for m in trailer["materiais"]] == ["Vector 8700"]
    assert [m["titulo"] for m in trailer["equipamentos"][0]["materiais"]] == ["Vector 8500"]


def test_linktree_oficial_mapeado_para_o_catalogo_seedado():
    seeds = [
        {"codigo": c, "linha_produto": l, "modelo_base": n, "nome_comercial": n}
        for c, l, n in [("VECTOR-8500", "TRAILER", "VECTOR 8500"), ("VECTOR-HE19", "TRAILER", "VECTOR HE 19"), ("X4-7700", "TRAILER", "X4 7700"),
                        ("X4-7500", "TRAILER", "X4 7500"), ("SUPRA-850", "DIESEL TRUCK", "SUPRA 850"), ("CITIMAX-D5", "DIRECT DRIVE", "CITIMAX D5")]
    ]
    resultado = vitrine.montar_vitrine(equipamentos=seeds, precos=[], materiais_conteudo=vitrine._materiais_brutos(), ver_precos=False, hoje=HOJE, fonte="catalogo_comercial")
    por_codigo = {e["codigo"]: [m["titulo"] for m in e["materiais"]] for l in resultado["linhas"] for e in l["equipamentos"]}
    assert por_codigo["X4-7500"] == ["Catálogo X4 7500"]
    assert por_codigo["VECTOR-HE19"] == ["Catálogo Vector HE 19"]
    assert por_codigo["CITIMAX-D5"] == ["Catálogo Citimax D"]
    linhas = {l["codigo"]: [m["titulo"] for m in l["materiais"]] for l in resultado["linhas"]}
    assert "Catálogo Vector 8700" in linhas["TRAILER"]
    assert {"Catálogo Supra", "Supra Series"} <= set(linhas["DIESEL TRUCK"])
    assert {"Catálogo Citimax", "Catálogo Xarios"} <= set(linhas["DIRECT DRIVE"])
    assert resultado["linktree_url"] == "https://linktr.ee/carriertransicoldbrasil"
    assert "Lynx Fleet (telemetria)" in [m["titulo"] for m in resultado["materiais_gerais"]]


@pytest.mark.parametrize("status_final", ["REALIZADA", "FINALIZADA", "NÃO REALIZADA", "NAO_REALIZADA", "Concluída"])
def test_atividade_com_status_terminal_nao_vira_followup_nem_proximo_passo(status_final):
    atividade = {"id": "a1", "status": status_final, "data": "2026-11-20", "oportunidade_id": "o1", "usuario_id": "vend-1"}
    vencida = {**atividade, "id": "a2", "data": "2026-10-20", "oportunidade_id": None}
    briefing = montar_briefing([_op("o1", data_fechamento_prevista="2026-12-20")], [atividade, vencida], hoje=HOJE)
    assert "FOLLOWUP_ATRASADO" not in briefing["sinais_por_codigo"]
    assert briefing["sinais_por_codigo"].get("SEM_PROXIMO_PASSO") == 1  # futura, mas já encerrada


def test_compromisso_que_apenas_venceu_nao_conta_como_contato():
    proposta = _op("o1", etapa="PROPOSTA", status_proposta="ENVIADA", data_fechamento_prevista="2026-12-20",
                   created_at="2026-09-01T00:00:00+00:00", updated_at="2026-09-10T00:00:00+00:00")
    pendente = {"id": "a1", "status": "PENDENTE", "data": "2026-11-06", "oportunidade_id": "o1", "created_at": "2026-09-10T00:00:00+00:00"}
    briefing = montar_briefing([proposta], [pendente], hoje=HOJE)
    assert "PROPOSTA_SEM_RETORNO" in briefing["sinais_por_codigo"]
    realizada = {**pendente, "status": "REALIZADA"}
    assert "PROPOSTA_SEM_RETORNO" not in montar_briefing([proposta], [realizada], hoje=HOJE)["sinais_por_codigo"]


def test_movimento_da_proposta_ou_do_pedido_conta_como_atividade_do_negocio():
    parada = _op("o1", data_fechamento_prevista="2026-12-20", created_at="2026-08-01T00:00:00+00:00", updated_at="2026-08-01T00:00:00+00:00")
    assert "OPORTUNIDADE_PARADA" in montar_briefing([parada], [], hoje=HOJE)["sinais_por_codigo"]
    com_proposta = {**parada, "proposta_atualizada_em": "2026-11-06T15:00:00+00:00"}
    assert "OPORTUNIDADE_PARADA" not in montar_briefing([com_proposta], [], hoje=HOJE)["sinais_por_codigo"]
    pedido = _op("o2", etapa="PEDIDO", pedido_id="p2", created_at="2026-08-01T00:00:00+00:00", updated_at="2026-08-01T00:00:00+00:00")
    assert "PEDIDO_SEM_MOVIMENTO" in montar_briefing([pedido], [], hoje=HOJE)["sinais_por_codigo"]
    assert "PEDIDO_SEM_MOVIMENTO" not in montar_briefing([{**pedido, "pedido_atualizado_em": "2026-11-05"}], [], hoje=HOJE)["sinais_por_codigo"]
