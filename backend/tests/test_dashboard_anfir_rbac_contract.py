from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "routers" / "anfir_workbook_router.py"
LAYOUT = ROOT / "frontend" / "src" / "app" / "layout.tsx"
BRIDGE = ROOT / "frontend" / "src" / "components" / "security" / "AuthenticatedAnfirFetchBridge.tsx"
ESTRATEGIA = ROOT / "backend" / "routers" / "crm_scope_estrategia_router.py"


def test_workbook_anfir_exige_usuario_e_reutiliza_escopo_territorial():
    source = BACKEND.read_text(encoding="utf-8")
    assert "Depends(usuario_atual)" in source
    assert "_anfir_do_usuario" in source
    assert 'contexto="viena-sp"' in source
    assert 'periodo="PERSONALIZADO"' in source
    assert "_metadata_escopo(usuario)" in source


def test_escopo_regional_continua_baseado_nos_ddds_cadastrados():
    source = ESTRATEGIA.read_text(encoding="utf-8")
    assert 'supabase.table("cti_users")' in source
    assert '.select("nome,ddds")' in source
    assert "permitidos = set(perfil[\"ddds\"])" in source
    assert "normalizar_ddd(item.get(\"ddd\") or item.get(\"codigo_ddd\")) in permitidos" in source


def test_frontend_autentica_as_leituras_existentes_sem_reescrever_dashboard():
    layout = LAYOUT.read_text(encoding="utf-8")
    bridge = BRIDGE.read_text(encoding="utf-8")
    assert "<AuthenticatedAnfirFetchBridge />" in layout
    assert 'ANFIR_WORKBOOK_PATH = "/api/cti/analytics/anfir-workbook-2026"' in bridge
    assert "supabase.auth.getSession()" in bridge
    assert 'headers.set("Authorization", `Bearer ${token}`)' in bridge
    assert "if (!url.includes(ANFIR_WORKBOOK_PATH))" in bridge


def test_correcao_nao_adiciona_escrita_na_base_anfir():
    source = BACKEND.read_text(encoding="utf-8")
    forbidden = ["insert(", "update(", "delete(", ".upsert(", ".insert(", ".update(", ".delete("]
    for token in forbidden:
        assert token not in source
