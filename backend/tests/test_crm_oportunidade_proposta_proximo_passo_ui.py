from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "crm-app" / "_components" / "NegociosNativos.tsx"


def test_oportunidade_exibe_proposta_e_proximo_passo_ate_pedido():
    page = PAGE.read_text(encoding="utf-8")
    assert "propostaId" in page
    assert "statusProposta" in page
    assert "pedidoId" in page
    assert "Próximo passo:" in page
    assert "Abrir proposta" in page
    assert "Abrir pedido" in page
    assert "/crm-app/propostas/" in page
    assert "/crm-app/pedidos/" in page
    assert "registrar o aceite do cliente e então converter em pedido" in page
