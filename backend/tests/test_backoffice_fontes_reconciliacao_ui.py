from pathlib import Path


def _frontend(path: str) -> str:
    raiz = Path(__file__).resolve().parents[2]
    return (raiz / "frontend" / "src" / "app" / "backoffice-fontes" / path).read_text(encoding="utf-8")


def test_backoffice_expoe_reconciliacao_so_para_candidato_operacional():
    fonte = _frontend("page.tsx")
    assert 'destino === "CANDIDATO_OPERACIONAL_VALIDACAO"' in fonte
    assert "Reconciliar" in fonte
    assert "ReconciliacaoFontePanel" in fonte


def test_painel_preserva_gate_master_e_separacao_dos_dominios():
    fonte = _frontend("ReconciliacaoFontePanel.tsx")
    assert "Promoção automática bloqueada" in fonte
    assert "ANFIR · mercado realizado" in fonte
    assert "CRM · processo comercial / origem do Funil" in fonte
    assert '"/reconciliacao/aprovar"' in fonte
    assert '"/reconciliacao/promover"' in fonte


def test_painel_so_libera_adaptadores_canonicos_atuais():
    fonte = _frontend("ReconciliacaoFontePanel.tsx")
    assert 'CTI_ANFIR::ANFIR' in fonte
    assert 'CRM_COMERCIAL::CLIENTE' in fonte
    assert "Promoção bloqueada: ainda não existe adaptador canônico seguro" in fonte
