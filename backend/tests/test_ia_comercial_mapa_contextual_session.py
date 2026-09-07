from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_interface_explica_que_contexto_e_da_sessao_atual():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "permanece nesta seleção e nesta sessão" in mapa
    assert "não grava uma nova conversa" in mapa
