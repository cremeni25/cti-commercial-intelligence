from services import ia_comercial_historico  # noqa: F401 - ativa registro da fonte
from services import ia_comercial_universo as universo
from services import ia_comercial_universo_historico as extensao


def _base_vazia(usuario_id, tipo_usuario):
    return {}, {"escopo_teste": True}


def test_catalogo_universal_expoe_historico_comercial_para_admin(monkeypatch):
    monkeypatch.setattr(extensao, "_ORIGINAL_CARREGAR_FONTES", _base_vazia)
    catalogo = universo.catalogar_universo_cti("admin", "ADMIN_MASTER")
    fonte = next(item for item in catalogo["fontes"] if item["fonte"] == "historico_comercial")

    assert fonte["total_registros_autorizados"] == 906
    assert "cliente" in fonte["campos_disponiveis"]
    assert "equipamento" in fonte["campos_disponiveis"]
    assert "representante_original" in fonte["campos_disponiveis"]
    assert "representante_atual" in fonte["campos_disponiveis"]
    assert "canal_venda" in fonte["campos_disponiveis"]
    assert "implementadora" in fonte["campos_disponiveis"]


def test_consulta_universal_filtra_e_agrega_historico_comercial(monkeypatch):
    monkeypatch.setattr(extensao, "_ORIGINAL_CARREGAR_FONTES", _base_vazia)

    consulta = universo.consultar_universo_cti(
        "admin",
        "ADMIN_MASTER",
        fonte="historico_comercial",
        termo="KONA TRANSPORTES",
        limite=50,
    )
    assert consulta["total_filtrado"] > 0
    assert any("KONA" in str(item.get("cliente")) for item in consulta["resultado"])

    agregado = universo.consultar_universo_cti(
        "admin",
        "ADMIN_MASTER",
        fonte="historico_comercial",
        filtros=[{"campo": "canal_venda", "operador": "eq", "valor": "INDIRETA_OEM"}],
        agrupar_por=["canal_venda"],
        metricas=[{"operacao": "count", "campo": None, "alias": "registros"}],
        limite=10,
    )
    assert agregado["total_filtrado"] == 111
    assert agregado["resultado"] == [{"canal_venda": "INDIRETA_OEM", "registros": 111}]


def test_historico_comercial_nao_amplia_rbac_de_outro_perfil(monkeypatch):
    monkeypatch.setattr(extensao, "_ORIGINAL_CARREGAR_FONTES", _base_vazia)
    catalogo = universo.catalogar_universo_cti("vendedor", "VENDEDOR")
    fonte = next(item for item in catalogo["fontes"] if item["fonte"] == "historico_comercial")
    assert fonte["total_registros_autorizados"] == 0
