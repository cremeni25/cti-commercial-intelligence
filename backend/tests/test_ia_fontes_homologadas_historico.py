from services.historical_commercial_source import (
    SOURCE_SHA256,
    carregar_historico_comercial,
    filtrar_historico_comercial,
    resumir_historico_comercial,
)
from services import ia_comercial_historico


def test_fonte_comercial_homologada_tem_906_registros_e_proveniencia():
    rows = carregar_historico_comercial()
    assert len(rows) == 906
    assert {row["arquivo_sha256"] for row in rows} == {SOURCE_SHA256}
    assert {row["aba_origem"] for row in rows} == {"BACKLOG", "OPORTUNIDADE", "INTERMEDIAÇÃO - OEM"}
    assert all(row["linha_origem"] and row["linha_origem"] >= 6 for row in rows)


def test_resumo_comercial_reproduz_controles_homologados():
    resumo = resumir_historico_comercial()
    assert resumo["total_registros"] == 906
    assert resumo["total_unidades"] == 3116
    assert resumo["valor_nominal"] == 193255897.4
    assert resumo["por_aba"] == {"OPORTUNIDADE": 518, "BACKLOG": 277, "INTERMEDIAÇÃO - OEM": 111}
    assert resumo["por_ano"] == {"2024": 381, "2025": 307, "2026": 185, "2023": 33}
    assert resumo["por_canal"] == {"DIRETA": 795, "INDIRETA_OEM": 111}
    assert resumo["regra_carla_monica"]["registros"] == 15
    assert resumo["regra_carla_monica"]["preserva_autoria_historica"] is True


def test_consulta_livre_encontra_cliente_e_canal_oem():
    clientes = filtrar_historico_comercial("KONA TRANSPORTES", limite=20)
    assert clientes
    assert any("KONA" in str(row.get("cliente")) for row in clientes)

    oem = filtrar_historico_comercial("INDIRETA_OEM", limite=200)
    assert len(oem) == 111
    assert all(row["canal_venda"] == "INDIRETA_OEM" for row in oem)


def test_contexto_historico_expoe_anfir_e_historico_comercial(monkeypatch):
    monkeypatch.setattr(ia_comercial_historico.repository, "buscar_cti_anfir", lambda: [])
    contexto = ia_comercial_historico.contexto_historico("ADMIN_MASTER")

    assert contexto["fonte"] == "Fontes homologadas CTI/ANFIR + Histórico Comercial 2023–2026"
    assert contexto["fontes"]["historico_comercial"]["total_registros"] == 906
    assert contexto["dashboard_historico"]["historico_comercial"]["total_registros"] == 906
    assert len(contexto["registros_consultaveis"]) == 906
    assert contexto["fontes"]["historico_comercial"]["nao_promove_crm"] is True
