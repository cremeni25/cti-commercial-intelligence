from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "ia_comercial_mapa_router.py"


def test_pergunta_do_usuario_entra_como_aprofundamento_do_contexto():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "PERGUNTA DO USUÁRIO" in fonte
    assert "aprofundamento da leitura atual" in fonte
    assert "não uma nova conversa genérica" in fonte
