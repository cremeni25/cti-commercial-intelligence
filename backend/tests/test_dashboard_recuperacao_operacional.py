from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "frontend" / "src" / "app" / "dashboard" / "page.tsx"
HISTORICO = ROOT / "frontend" / "src" / "app" / "historico-comercial" / "page.tsx"


def test_dashboard_nao_converte_indisponibilidade_em_zero():
    fonte = DASHBOARD.read_text(encoding="utf-8")

    assert "RETRY_MS = 5_000" in fonte
    assert "nenhum indicador indisponível será mostrado como zero" in fonte
    assert 'historicoDisponivel ? String(historico.metadata?.total_registros_filtrados ?? 0) : "—"' in fonte
    assert 'nucleoDisponivel ? abertos.length : "—"' in fonte
    assert "window.addEventListener(\"online\", aoReconectar)" in fonte


def test_historico_explicita_que_e_somente_consulta():
    fonte = HISTORICO.read_text(encoding="utf-8")

    assert "SOMENTE CONSULTA · NÃO ALTERA O CRM" in fonte
    assert "Base histórica consolidada para consulta e auditoria." in fonte
    assert "HIST-006" not in fonte
    assert "HIST-007" not in fonte
    assert "READ-ONLY · NÃO PROMOVIDO" not in fonte
