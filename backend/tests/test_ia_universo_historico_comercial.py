from services import ia_comercial_universo as universo
from services.anfir_market_scope import implementadora_fora_escopo
from services.historical_commercial_source import carregar_historico_comercial


def _isolar_fontes_externas(monkeypatch):
    monkeypatch.setattr(universo, "_escopo_autorizado", lambda usuario_id, tipo_usuario: {})
    monkeypatch.setattr(universo.repository, "buscar_cti_anfir", lambda: [])
    monkeypatch.setattr(universo, "_aplicar_rbac", lambda registros, usuario_id, tipo_usuario, escopo: ([], {"teste": True}, None))
    monkeypatch.setattr(universo, "_consulta_segura", lambda tabela: [])
    monkeypatch.setattr(universo, "_fonte_catalogo_produtos", lambda: [])
    monkeypatch.setattr(universo, "_fonte_perfil_usuario", lambda usuario_id: [])


def test_catalogo_universal_expoe_historico_comercial_filtrado_para_admin(monkeypatch):
    _isolar_fontes_externas(monkeypatch)
    catalogo = universo.catalogar_universo_cti("admin", "ADMIN_MASTER")
    fonte = next(item for item in catalogo["fontes"] if item["fonte"] == "historico_comercial")

    assert fonte["total_registros_autorizados"] == len(carregar_historico_comercial())
    assert "cliente" in fonte["campos_disponiveis"]
    assert "equipamento" in fonte["campos_disponiveis"]
    assert "representante_original" in fonte["campos_disponiveis"]
    assert "representante_atual" in fonte["campos_disponiveis"]
    assert "canal_venda" in fonte["campos_disponiveis"]
    assert "implementadora" in fonte["campos_disponiveis"]


def test_consulta_universal_filtra_e_agrega_historico_comercial(monkeypatch):
    _isolar_fontes_externas(monkeypatch)

    consulta = universo.consultar_universo_cti(
        "admin",
        "ADMIN_MASTER",
        fonte="historico_comercial",
        termo="KONA TRANSPORTES",
        limite=50,
    )
    assert consulta["total_filtrado"] > 0
    assert any("KONA" in str(item.get("cliente")) for item in consulta["resultado"])
    assert all(implementadora_fora_escopo(item) is None for item in consulta["resultado"])

    agregado = universo.consultar_universo_cti(
        "admin",
        "ADMIN_MASTER",
        fonte="historico_comercial",
        filtros=[{"campo": "canal_venda", "operador": "eq", "valor": "INDIRETA_OEM"}],
        agrupar_por=["canal_venda"],
        metricas=[{"operacao": "count", "campo": None, "alias": "registros"}],
        limite=10,
    )
    assert agregado["total_filtrado"] > 0
    assert agregado["resultado"] == [{"canal_venda": "INDIRETA_OEM", "registros": agregado["total_filtrado"]}]


def test_historico_comercial_nao_amplia_rbac_de_outro_perfil(monkeypatch):
    _isolar_fontes_externas(monkeypatch)
    catalogo = universo.catalogar_universo_cti("vendedor", "VENDEDOR")
    fonte = next(item for item in catalogo["fontes"] if item["fonte"] == "historico_comercial")
    assert fonte["total_registros_autorizados"] == 0
