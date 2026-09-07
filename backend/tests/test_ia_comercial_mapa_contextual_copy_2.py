from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_aprofundamento_permanece_no_fluxo_atual():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Pergunte sobre esta leitura" in mapa
    assert "Perguntar" in mapa
    assert "/ia-comercial" not in mapa
