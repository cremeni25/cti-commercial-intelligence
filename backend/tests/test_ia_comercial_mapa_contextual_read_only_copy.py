from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_interface_informa_que_nao_altera_crm():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "não altera CRM" in mapa
    assert "não cria oportunidade" in mapa
