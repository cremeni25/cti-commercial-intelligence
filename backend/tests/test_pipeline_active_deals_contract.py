from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PIPELINE_PAGE = ROOT / "frontend" / "src" / "app" / "pipeline" / "page.tsx"


def test_pipeline_preserva_negociacoes_ativas_sem_filtro_temporal_explicito():
    source = PIPELINE_PAGE.read_text(encoding="utf-8")
    assert "aplicarFiltrosComerciais" in source
    assert "FILTROS_CRM_VAZIOS" in source
    assert "dataPrevista" in source


def test_pipeline_permite_filtro_explicito_por_data_prevista_sem_remover_a_previsao_da_tela():
    source = PIPELINE_PAGE.read_text(encoding="utf-8")
    assert "CrmFiltrosComerciais" in source
    assert "dataPrevista" in source
    assert "calcularMetricasPrazo" in source
