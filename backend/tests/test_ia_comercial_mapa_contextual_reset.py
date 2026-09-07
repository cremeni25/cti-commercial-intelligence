from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_atualizacao_da_leitura_base_limpa_aprofundamentos_transitorios():
    mapa = MAPA.read_text(encoding="utf-8")
    inicio = mapa.index("async function carregarInteligencia")
    fim = mapa.index("async function perguntarContexto")
    trecho = mapa[inicio:fim]
    assert "setHistoricoContextual([])" in trecho
