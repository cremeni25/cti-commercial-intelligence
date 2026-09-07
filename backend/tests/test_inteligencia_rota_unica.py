from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIDEBAR = ROOT / "frontend" / "src" / "components" / "ui" / "Sidebar.tsx"
HUB = ROOT / "frontend" / "src" / "app" / "inteligencia-comercial" / "page.tsx"


def test_sidebar_separa_mapa_estrategico_de_ia_comercial():
    sidebar = SIDEBAR.read_text(encoding="utf-8")
    assert '"pt-BR": "Mapa Estratégico"' in sidebar
    assert 'href: "/mapa-estrategico"' in sidebar
    assert 'href: "/ia-comercial"' in sidebar
    assert '"pt-BR": "Inteligência Comercial"' not in sidebar


def test_rota_legada_de_inteligencia_redireciona_para_mapa_aprovado():
    hub = HUB.read_text(encoding="utf-8")
    assert 'redirect("/mapa-estrategico")' in hub
    assert "visualizacoes" not in hub
    assert "Abrir IA Comercial" not in hub
