from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "ia_comercial_mapa_router.py"
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_contextual_e_transitorio_e_embutido():
    router = ROUTER.read_text(encoding="utf-8")
    mapa = MAPA.read_text(encoding="utf-8")
    assert '"persistido": False' in router
    assert "cti_ia_conversas" not in router
    assert "/ia-comercial" not in mapa
    assert "Pergunte sobre esta leitura" in mapa
