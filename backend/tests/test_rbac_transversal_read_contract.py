from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "frontend" / "src" / "lib" / "crm-canonical.ts"
BRIDGE = ROOT / "frontend" / "src" / "components" / "security" / "AuthenticatedAnfirFetchBridge.tsx"
SCOPE = ROOT / "backend" / "routers" / "crm_scope_router.py"


def test_listagens_documentais_e_operacionais_usam_rotas_seguras():
    canonical = CANONICAL.read_text(encoding="utf-8")
    assert 'caminho === "crm-documentos/propostas"' in canonical
    assert 'caminho === "crm-documentos/pedidos"' in canonical
    assert 'caminho === "carrier-operacional/pedidos"' in canonical
    assert 'caminho === "carrier-operacional/ciclos"' in canonical
    assert 'return "crm-seguro/propostas"' in canonical
    assert 'return "crm-seguro/pedidos"' in canonical
    assert 'return "crm-seguro/ciclos"' in canonical


def test_bridge_intercepta_leituras_legadas_que_antes_devolviam_dados_globais():
    bridge = BRIDGE.read_text(encoding="utf-8")
    for rota in (
        '"/vendas": "crm-seguro/vendas"',
        '"/crm-documentos/propostas": "crm-seguro/propostas"',
        '"/crm-documentos/pedidos": "crm-seguro/pedidos"',
        '"/carrier-operacional/pedidos": "crm-seguro/pedidos"',
        '"/carrier-operacional/ciclos": "crm-seguro/ciclos"',
    ):
        assert rota in bridge
    assert 'carrier-operacional\\/pedidos\\/([^/]+)\\/ciclo' in bridge
    assert 'crm-seguro/pedidos/${encodeURIComponent(cicloPedido[1])}/ciclo' in bridge


def test_backend_expoe_ciclos_somente_de_pedidos_autorizados():
    scope = SCOPE.read_text(encoding="utf-8")
    assert '@router.get("/ciclos")' in scope
    assert "pedidos_permitidos" in scope
    assert "_filtrar_por_usuario(listar_pedidos_operacionais(), usuario)" in scope
    assert 'str(item.get("id")) in pedidos_permitidos' in scope
    assert '@router.get("/pedidos/{pedido_id}/ciclo")' in scope
    assert "_pedido_autorizado(pedido_id, usuario)" in scope
