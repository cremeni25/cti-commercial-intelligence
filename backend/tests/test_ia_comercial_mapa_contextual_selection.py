from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_contexto_transitorio_nao_sobrevive_troca_de_responsavel():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "setHistoricoContextual([])" in mapa
    assert "setPerguntaContextual(\"\")" in mapa
