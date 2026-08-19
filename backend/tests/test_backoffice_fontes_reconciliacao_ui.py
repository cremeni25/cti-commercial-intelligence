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


def test_painel_permite_resolver_conflito_sem_promocao_direta():
    fonte = _frontend("ReconciliacaoFontePanel.tsx")
    assert "Resolver conflito" in fonte
    assert "/reconciliacao/itens/${itemEmEdicao.id}/resolver" in fonte
    assert "dados_normalizados" in fonte
    assert "motivo: motivoEdicao.trim()" in fonte
    assert "O backend reclassifica entidade, natureza e camada" in fonte
    assert "Uma nova aprovação será obrigatória antes da promoção" in fonte


def test_painel_evidencia_campo_valor_atual_e_valor_recebido_do_conflito():
    fonte = _frontend("ReconciliacaoFontePanel.tsx")
    assert "divergenciasDoItem" in fonte
    assert "Detalhes do conflito" in fonte
    assert "Campo em conflito" in fonte
    assert "Valor atual" in fonte
    assert "Valor recebido" in fonte
    assert "valor_existente" in fonte
    assert "valor_recebido" in fonte
