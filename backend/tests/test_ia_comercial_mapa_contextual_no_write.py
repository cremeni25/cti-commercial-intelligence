from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "ia_comercial_mapa_router.py"


def test_router_contextual_permanece_somente_leitura():
    fonte = ROUTER.read_text(encoding="utf-8")
    proibidos = [
        ".insert(",
        ".update(",
        ".delete(",
        "cti_ia_conversas",
        "cti_ia_mensagens",
        "criar_oportunidade",
        "atualizar_oportunidade",
    ]
    for termo in proibidos:
        assert termo not in fonte
    assert '"somente_leitura": True' in fonte
    assert '"persistido": False' in fonte
