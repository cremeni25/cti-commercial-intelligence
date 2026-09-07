from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_interface_nao_se_apresenta_como_nova_ia_ou_chatbot():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Nova IA" not in mapa
    assert "Chatbot" not in mapa
    assert "Leitura contextual" in mapa
    assert "O que os dados estão mostrando" in mapa
