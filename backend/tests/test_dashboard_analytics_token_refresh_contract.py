from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "frontend" / "src" / "components" / "security" / "AuthenticatedAnfirFetchBridge.tsx"


def test_bridge_protege_todas_as_leituras_analytics_do_dashboard():
    source = BRIDGE.read_text(encoding="utf-8")
    assert 'CTI_ANALYTICS_PATH = "/api/cti/analytics/"' in source
    assert "url.includes(CTI_ANALYTICS_PATH)" in source
    assert 'headers.set("Authorization", `Bearer ${token}`)' in source


def test_bridge_renova_token_expirado_e_repete_leitura_uma_vez():
    source = BRIDGE.read_text(encoding="utf-8")
    assert "resposta.status !== 401" in source
    assert "supabase.auth.refreshSession()" in source
    assert "tokenRenovado" in source
    assert 'headersRenovados.set("Authorization", `Bearer ${tokenRenovado}`)' in source
    assert "return originalFetch(input, { ...init, headers: headersRenovados })" in source


def test_bridge_nao_repete_escritas_apos_401():
    source = BRIDGE.read_text(encoding="utf-8")
    assert 'const leituraSegura = metodo === "GET" || metodo === "HEAD"' in source
    assert "resposta.status !== 401 || !leituraSegura" in source
