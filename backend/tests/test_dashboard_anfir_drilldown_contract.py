from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend" / "src" / "components" / "AnfirWorkbookPanel.tsx"
DRILL = ROOT / "backend" / "routers" / "drilldown_router.py"
SECURE = ROOT / "backend" / "routers" / "crm_scope_estrategia_router.py"


def test_dashboard_anfir_expoe_rastreabilidade_nos_indicadores():
    painel = PANEL.read_text(encoding="utf-8")
    assert 'Clique para detalhar' in painel
    assert 'campo:"categoria",valor:"CARRIER"' in painel
    assert 'campo:"categoria",valor:"SEM_CONTATO"' in painel
    assert 'campo:"causa",valor:"COBERTURA_COMERCIAL"' in painel
    assert 'campo:"categoria",valor:"NAO_CLASSIFICADO"' in painel
    assert 'campo:"tema",valor:r.tema' in painel
    assert 'campo:"observacao",valor:"COM_OBSERVACAO"' in painel
    assert 'campo:"observacao",valor:"SEM_OBSERVACAO"' in painel
    assert 'contexto:"viena-sp"' in painel
    assert 'inicio:"2026-01-01"' in painel
    assert 'fim:"2026-12-31"' in painel


def test_drilldown_reutiliza_semantica_do_workbook_auditado():
    drill = DRILL.read_text(encoding="utf-8")
    seguro = SECURE.read_text(encoding="utf-8")
    assert 'categoria_workbook_2026' in drill
    assert 'causa_workbook_2026' in drill
    assert 'temas_workbook_2026' in drill
    assert 'extrair_observacao_workbook' in drill
    assert '"trimestre": ()' in drill
    assert '_ddd_workbook(item) == alvo' in drill
    assert 'drill._filtrar_anfir_semantico' in seguro


def test_rastreabilidade_nao_altera_fontes_ou_persistencia():
    drill = DRILL.read_text(encoding="utf-8")
    forbidden = ["insert(", "update(", "delete(", ".upsert(", ".insert(", ".update(", ".delete("]
    for token in forbidden:
        assert token not in drill
