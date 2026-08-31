from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_graficos_anfir_usam_token_e_nao_somem_se_competitividade_falhar():
    source = (ROOT / "frontend/src/components/AnfirWorkbookCharts.tsx").read_text(encoding="utf-8")
    assert "getSupabaseClient" in source
    assert 'Authorization:`Bearer ${token}`' in source
    assert "Promise.allSettled" in source
    assert "Gráficos ANFIR indisponíveis" in source
    assert "Inteligência competitiva ainda não carregou" in source
    assert "Carrier × concorrência por fabricante" in source
    assert "Trailer · Carrier × concorrência" not in source  # títulos são gerados por dados, não hardcoded por linha


def test_relatorio_competitivo_usa_sessao_autenticada():
    source = (ROOT / "frontend/src/app/dashboard/anfir-competitividade-relatorio/page.tsx").read_text(encoding="utf-8")
    assert "getSupabaseClient" in source
    assert 'Authorization:`Bearer ${token}`' in source
    assert "Relatório de Inteligência Competitiva" in source
    assert "Imprimir / Salvar PDF" in source
