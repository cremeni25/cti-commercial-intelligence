from services.historical_commercial_source import (
    SOURCE_SHA256,
    carregar_historico_comercial,
    carregar_historico_comercial_bruto,
    filtrar_historico_comercial,
    resumir_historico_comercial,
)
from services.anfir_market_scope import implementadora_fora_escopo
from services import ia_comercial_historico


def test_fonte_bruta_homologada_preserva_906_registros_e_proveniencia():
    rows = carregar_historico_comercial_bruto()
    assert len(rows) == 906
    assert {row["arquivo_sha256"] for row in rows} == {SOURCE_SHA256}
    assert {row["aba_origem"] for row in rows} == {"BACKLOG", "OPORTUNIDADE", "INTERMEDIAÇÃO - OEM"}
    assert all(row["linha_origem"] and row["linha_origem"] >= 6 for row in rows)


def test_universo_comercial_aplica_regra_global_mercado_real_viena():
    rows = carregar_historico_comercial()
    assert len(rows) <= 906
    assert all(implementadora_fora_escopo(row) is None for row in rows)


def test_resumo_bruto_continua_auditavel_e_resumo_comercial_e_filtrado():
    bruto = resumir_historico_comercial(carregar_historico_comercial_bruto())
    assert bruto["total_registros"] == 906
    assert bruto["total_unidades"] == 3116
    assert bruto["valor_nominal"] == 193255897.4
    assert bruto["por_aba"] == {"OPORTUNIDADE": 518, "BACKLOG": 277, "INTERMEDIAÇÃO - OEM": 111}
    assert bruto["por_ano"] == {"2024": 381, "2025": 307, "2026": 185, "2023": 33}
    assert bruto["por_canal"] == {"DIRETA": 795, "INDIRETA_OEM": 111}
    assert bruto["regra_carla_monica"]["registros"] == 15
    assert bruto["regra_carla_monica"]["preserva_autoria_historica"] is True

    comercial = resumir_historico_comercial()
    assert comercial["regra_mercado"] == "MERCADO_REAL_VIENA"
    assert comercial["total_registros"] == len(carregar_historico_comercial())


def test_consulta_livre_encontra_cliente_e_canal_oem_no_mercado_real():
    clientes = filtrar_historico_comercial("KONA TRANSPORTES", limite=20)
    assert clientes
    assert any("KONA" in str(row.get("cliente")) for row in clientes)

    oem = filtrar_historico_comercial("INDIRETA_OEM", limite=200)
    assert oem
    assert all(row["canal_venda"] == "INDIRETA_OEM" for row in oem)
    assert all(implementadora_fora_escopo(row) is None for row in oem)


def test_contexto_historico_expoe_apenas_mercado_real_viena(monkeypatch):
    monkeypatch.setattr(ia_comercial_historico.repository, "buscar_cti_anfir", lambda: [])
    contexto = ia_comercial_historico.contexto_historico("ADMIN_MASTER")
    esperado = len(carregar_historico_comercial())

    assert contexto["fonte"] == "Fontes homologadas CTI/ANFIR + Histórico Comercial 2023–2026"
    assert contexto["fontes"]["historico_comercial"]["total_registros"] == esperado
    assert contexto["dashboard_historico"]["historico_comercial"]["total_registros"] == esperado
    assert len(contexto["registros_consultaveis"]) == esperado
    assert all(implementadora_fora_escopo(row) is None for row in contexto["registros_consultaveis"])
    assert contexto["fontes"]["historico_comercial"]["nao_promove_crm"] is True
