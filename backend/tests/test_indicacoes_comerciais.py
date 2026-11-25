"""Indicadores, indicações e comissões (dados fictícios)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.admin_auth import UsuarioAutenticado, usuario_atual
from services import indicacoes_comerciais as ind
from tests import cofre_falso, supabase_memoria


@pytest.fixture
def ambiente(monkeypatch):
    dados = {
        "cti_oportunidades": [
            {"id": "op-ganha", "status": "GANHO", "valor_total": 480000, "data_fechamento_real": "2026-10-20", "arquivado_em": None},
            {"id": "op-perdida", "status": "PERDIDO", "valor_total": 1, "arquivado_em": None},
            {"id": "op-aberta", "status": "PROPOSTA", "valor_total": 1, "arquivado_em": None},
            {"id": "op-outra", "status": "GANHO", "valor_total": 520000, "data_fechamento_real": "2026-10-02", "arquivado_em": None},
        ],
    }
    monkeypatch.setattr("core.supabase_client.supabase", supabase_memoria.criar(dados))
    cofre_falso.instalar(monkeypatch)
    monkeypatch.setattr("services.planilhas_comerciais.registros", lambda fonte: [{"quantidade": 8, "data_emissao": "2026-10-05"}] if fonte == "vendas_realizadas" else [])
    ind._limpar_cache()
    yield dados
    ind._limpar_cache()


def _indicador(nome="João Indicador", **extra):
    return ind.salvar_indicador({"nome": nome, "documento": extra.pop("documento", None), **extra}, "gestor")


def _indicacao(indicador_id, linha="TRAILER", quantidade=2, valor=400000, regiao="Campinas", **extra):
    return ind.registrar_indicacao({"indicador_id": indicador_id, "cliente_nome": "Frios Alfa", "regiao": regiao, "linha": linha,
                                    "modelo": "VECTOR HE19", "quantidade": quantidade, "valor_final": valor, **extra}, "gestor")


def test_tabela_de_comissao_por_linha():
    assert ind.comissao("Trailer", 2) == 2800
    assert ind.comissao("DT", 3) == 2700
    assert ind.comissao("direct drive", 5) == 2000
    with pytest.raises(ind.ErroIndicacao):
        ind.normalizar_linha("Reefer")


def test_ciclo_venda_nota_fiscal_e_pagamento(ambiente):
    joao = _indicador()
    i = _indicacao(joao["id"])
    assert i["status"] == "INDICADA" and i["comissao_valor"] is None
    with pytest.raises(ind.ErroIndicacao):  # comissão só depois da venda
        ind.atualizar_indicacao(i["id"], {"comissao_status": "NF_RECEBIDA", "nota_fiscal": "123"}, "gestor")
    v = ind.atualizar_indicacao(i["id"], {"status": "VENDIDA", "data_venda": "2026-10-10"}, "gestor")
    assert v["comissao_unitaria"] == 1400 and v["comissao_valor"] == 2800 and v["comissao_status"] == "A_PAGAR"
    with pytest.raises(ind.ErroIndicacao):  # paga só com NF
        ind.atualizar_indicacao(i["id"], {"comissao_status": "PAGA"}, "gestor")
    with pytest.raises(ind.ErroIndicacao):
        ind.atualizar_indicacao(i["id"], {"comissao_status": "NF_RECEBIDA"}, "gestor")
    ind.atualizar_indicacao(i["id"], {"comissao_status": "NF_RECEBIDA", "nota_fiscal": "NF 987"}, "gestor")
    with pytest.raises(ind.ErroIndicacao):  # venda com NF não se desfaz
        ind.atualizar_indicacao(i["id"], {"status": "PERDIDA"}, "gestor")
    pago = ind.atualizar_indicacao(i["id"], {"comissao_status": "PAGA", "paga_em": "2026-11-05"}, "gestor")
    assert pago["comissao_status"] == "PAGA" and pago["nota_fiscal"] == "NF 987" and len(pago["historico"]) == 4
    with pytest.raises(ind.ErroIndicacao):
        ind.atualizar_indicacao(i["id"], {"quantidade": 5}, "gestor")
    for volta in ({"comissao_status": "NF_RECEBIDA", "nota_fiscal": "NF 1"}, {"comissao_status": "A_PAGAR"}):
        with pytest.raises(ind.ErroIndicacao):  # comissão paga não reabre
            ind.atualizar_indicacao(i["id"], volta, "gestor")


def test_valor_por_equipamento_fica_gravado_na_venda(ambiente, monkeypatch):
    i = _indicacao(_indicador()["id"], linha="DIESEL TRUCK", quantidade=1)
    ind.atualizar_indicacao(i["id"], {"status": "VENDIDA"}, "gestor")
    monkeypatch.setitem(ind.COMISSAO_POR_LINHA, "DIESEL TRUCK", 1000.0)  # tabela muda depois
    r = ind.atualizar_indicacao(i["id"], {"quantidade": 2}, "gestor")
    assert r["comissao_unitaria"] == 900 and r["comissao_valor"] == 1800


def test_sincroniza_com_oportunidade(ambiente):
    joao = _indicador()
    ganha = _indicacao(joao["id"], valor=0, oportunidade_id="op-ganha")
    perdida = _indicacao(joao["id"], oportunidade_id="op-perdida")
    aberta = _indicacao(joao["id"], oportunidade_id="op-aberta")
    assert ind.sincronizar_com_oportunidades() == 3
    _, todas = ind._todos()
    assert todas[ganha["id"]]["status"] == "VENDIDA" and todas[ganha["id"]]["valor_final"] == 480000 and todas[ganha["id"]]["data_venda"] == "2026-10-20"
    assert todas[perdida["id"]]["status"] == "PERDIDA" and todas[aberta["id"]]["status"] == "EM_NEGOCIACAO"
    assert ind.sincronizar_com_oportunidades() == 0


def test_painel_por_indicador_regiao_linha_e_peso(ambiente):
    joao, maria = _indicador(), _indicador("Maria Indica", documento="12345678901")
    a = _indicacao(joao["id"], quantidade=2, valor=400000, regiao="Campinas")
    b = _indicacao(maria["id"], linha="DIRECT DRIVE", quantidade=3, valor=150000, regiao="Santos")
    _indicacao(maria["id"], linha="DIESEL TRUCK", quantidade=1, valor=90000, regiao="Santos")
    for x in (a, b):
        ind.atualizar_indicacao(x["id"], {"status": "VENDIDA", "data_venda": "2026-10-15"}, "gestor")
    p = ind.painel(2026, 10)
    t = p["total"]
    assert t["vendidas"] == 2 and t["equipamentos_vendidos"] == 5 and t["valor_vendido"] == 550000
    assert t["comissao_total"] == 2800 + 1200 and t["comissao_a_pagar"] == 4000
    assert p["peso_nas_vendas"]["valor_vendido_viena"] == 1000000 and p["peso_nas_vendas"]["participacao_valor"] == 0.55
    assert p["peso_nas_vendas"]["participacao_equipamentos"] == round(5 / 8, 4)
    assert [l["nome"] for l in p["por_indicador"]] == ["João Indicador", "Maria Indica"]
    assert {r["regiao"]: r["participacao_no_indicado"] for r in p["por_regiao"]} == {"Campinas": round(400000 / 550000, 4), "Santos": round(150000 / 550000, 4)}
    linhas = {l["linha"]: l for l in p["por_linha"]}
    assert linhas["DIRECT DRIVE"]["comissao_total"] == 1200 and linhas["TRAILER"]["comissao_por_equipamento"] == 1400
    e = ind.extrato(maria["id"])
    assert e["resumo"]["indicacoes"] == 2 and e["resumo"]["em_aberto"] == 1


def test_documento_duplicado_e_validacoes(ambiente):
    _indicador(documento="123.456.789-01")
    with pytest.raises(ind.ErroIndicacao):
        _indicador("Outro", documento="12345678901")
    with pytest.raises(ind.ErroIndicacao):
        _indicador("Doc ruim", documento="123")
    with pytest.raises(ind.ErroIndicacao):
        ind.registrar_indicacao({"indicador_id": "nao-existe", "cliente_nome": "X", "regiao": "Y", "linha": "TRAILER", "quantidade": 1, "valor_final": 1}, "g")


def _cliente(perfil):
    app = FastAPI()
    from routers.indicacoes_router import router

    app.include_router(router)
    app.dependency_overrides[usuario_atual] = lambda: perfil
    return TestClient(app)


def _usuario(tipo, permissoes=None, uid="u1"):
    return UsuarioAutenticado(id=uid, auth_id=uid, email=f"{uid}@example.invalid", nome=uid, tipo_usuario=tipo, permissoes=permissoes or {})


def test_somente_o_master_acessa(ambiente):
    maria = _indicador("Maria Indica")
    master = _cliente(_usuario("ADMIN_MASTER"))
    criada = master.post("/crm-seguro/indicacoes", json={"indicador_id": maria["id"], "cliente_nome": "Gama", "regiao": "Santos", "linha": "Trailer", "quantidade": 1, "valor_final": 200000}).json()
    assert master.patch(f"/crm-seguro/indicacoes/{criada['id']}", json={"status": "VENDIDA"}).json()["comissao_valor"] == 1400
    assert master.get("/crm-seguro/indicacoes/painel").status_code == 200
    assert master.get("/crm-seguro/indicacoes/acesso").json()["tabela_comissao"]["TRAILER"] == 1400
    csv = master.get(f"/crm-seguro/indicacoes/indicadores/{maria['id']}/extrato.csv")
    assert csv.status_code == 200 and "Gama;Santos;TRAILER" in csv.text and "1400,00" in csv.text

    outros = [
        _usuario("DIRETOR_VIENA_SP", {"acesso_total": True}, "d1"),
        _usuario("REPRES_REGIAO_01", {"oportunidades_editar": True, "oportunidades_visualizar": True}, "v1"),
        _usuario("INDICADOR_VIENA_SP", {"oportunidades_visualizar": True}, "i1"),
    ]
    for perfil in outros:
        c = _cliente(perfil)
        assert c.get("/crm-seguro/indicacoes").status_code == 403
        assert c.get("/crm-seguro/indicacoes/acesso").status_code == 403
        assert c.get("/crm-seguro/indicacoes/painel").status_code == 403
        assert c.get(f"/crm-seguro/indicacoes/indicadores/{maria['id']}/extrato").status_code == 403
        assert c.post("/crm-seguro/indicacoes", json={"indicador_id": maria["id"], "cliente_nome": "X", "regiao": "Y", "linha": "DD", "quantidade": 1, "valor_final": 1}).status_code == 403
        assert c.patch(f"/crm-seguro/indicacoes/{criada['id']}", json={"status": "PERDIDA"}).status_code == 403


def test_varias_indicacoes_na_mesma_oportunidade(ambiente):
    joao, maria = _indicador(), _indicador("Maria Indica")
    a = _indicacao(joao["id"], oportunidade_id="op-ganha")
    b = _indicacao(maria["id"], oportunidade_id="op-ganha")
    assert ind.sincronizar_com_oportunidades() == 2
    _, todas = ind._todos()
    assert todas[a["id"]]["status"] == todas[b["id"]]["status"] == "VENDIDA"


def test_leitura_sincroniza_com_oportunidade(ambiente):
    joao = _indicador()
    i = _indicacao(joao["id"], oportunidade_id="op-ganha")
    extrato = _cliente(_usuario("ADMIN_MASTER")).get(f"/crm-seguro/indicacoes/indicadores/{joao['id']}/extrato").json()
    assert extrato["indicacoes"][0]["id"] == i["id"] and extrato["indicacoes"][0]["status"] == "VENDIDA"
