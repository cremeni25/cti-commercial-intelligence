from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "ia_comercial_mapa_router.py"


def test_pergunta_contextual_preserva_separacao_temporal_das_fontes():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "ANFIR representa mercado realizado/referência" in fonte
    assert "nunca deve virar oportunidade automática" in fonte
    assert "Histórico/Funil representa fatos comerciais anteriores" in fonte
    assert "CRM representa negócios atuais em andamento" in fonte
    assert "Não atribua autoria ou território sem evidência" in fonte
    assert "Não invente vínculos entre fontes" in fonte
