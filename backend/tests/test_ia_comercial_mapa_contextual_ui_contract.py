from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_conversa_fica_embutida_na_leitura_sem_nova_rota_ou_menu():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Pergunte sobre esta leitura" in mapa
    assert "historicoContextual" in mapa
    assert "perguntarContexto" in mapa
    assert "/ia-comercial?prompt=" not in mapa
    assert "Aprofundar na IA" not in mapa
    assert "window.location" not in mapa


def test_troca_de_responsavel_descarta_contexto_transitorio_anterior():
    mapa = MAPA.read_text(encoding="utf-8")
    trecho = mapa[mapa.index("function trocarResponsavel"):mapa.index("return (", mapa.index("function trocarResponsavel"))]
    assert "setHistoricoContextual([])" in trecho
    assert "setPerguntaContextual(\"\")" in trecho
