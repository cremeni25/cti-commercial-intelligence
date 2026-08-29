from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "crm-app" / "_components" / "NegociosNativos.tsx"


def test_oportunidade_exibe_proposta_e_proximo_passo_ate_pedido():
    page = PAGE.read_text(encoding="utf-8")
    # O contrato é funcional: proposta/pedido e orientação de próximo passo
    # precisam continuar presentes, sem prender a UI a um idioma específico.
    assert "propostaId" in page
    assert "statusProposta" in page
    assert "pedidoId" in page
    assert "proximoPasso" in page
    assert "t.next" in page
    assert "t.openProposal" in page
    assert "t.openOrder" in page
    assert "/crm-app/propostas/" in page
    assert "/crm-app/pedidos/" in page
    assert "registerAcceptance" in page
