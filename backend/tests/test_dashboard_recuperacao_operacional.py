from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "frontend" / "src" / "app" / "dashboard" / "page.tsx"
HISTORICO = ROOT / "frontend" / "src" / "app" / "historico-comercial" / "page.tsx"
CATALOGO_ESTRATEGICO = ROOT / "frontend" / "src" / "core" / "i18n" / "strategic.ts"


def test_dashboard_executivo_nao_repete_operacao_crm_e_mantem_anfir_2026():
    fonte = DASHBOARD.read_text(encoding="utf-8")

    assert "AnfirWorkbookPanel" in fonte
    assert "AnfirWorkbookCharts" in fonte
    assert "/dashboard/anfir-historico" in fonte
    assert "crm/nucleo-comercial" not in fonte
    assert "crm/oportunidades" not in fonte
    assert "pipelineAberto" not in fonte
    assert "negociacoesAtivas" not in fonte
    assert "RETRY_MS" not in fonte


def test_historico_explicita_que_e_somente_consulta():
    fonte = HISTORICO.read_text(encoding="utf-8")
    catalogo = CATALOGO_ESTRATEGICO.read_text(encoding="utf-8")

    assert 't("history.readOnly")' in fonte
    assert 't("history.subtitle")' in fonte
    assert "SOMENTE CONSULTA · NÃO ALTERA O CRM" in catalogo
    assert "Base histórica consolidada para consulta e auditoria." in catalogo
    assert "READ ONLY · DOES NOT CHANGE CRM" in catalogo
    assert "SOLO CONSULTA · NO MODIFICA EL CRM" in catalogo
    assert "HIST-006" not in fonte
    assert "HIST-007" not in fonte
    assert "READ-ONLY · NÃO PROMOVIDO" not in fonte
