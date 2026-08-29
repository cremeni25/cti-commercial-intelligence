from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "frontend" / "src" / "app" / "dashboard" / "page.tsx"
HISTORICO = ROOT / "frontend" / "src" / "app" / "historico-comercial" / "page.tsx"
CATALOGO_OPERACIONAL = ROOT / "frontend" / "src" / "core" / "i18n" / "operational.ts"


def test_dashboard_nao_converte_indisponibilidade_em_zero():
    fonte = DASHBOARD.read_text(encoding="utf-8")
    catalogo = CATALOGO_OPERACIONAL.read_text(encoding="utf-8")

    assert re.search(r"RETRY_MS\s*=\s*5_000", fonte)
    assert 'tOp("dashboard.connection")' in fonte
    assert "nenhum indicador indisponível será mostrado como zero" in catalogo
    assert re.search(r"historicoDisponivel\?formatNumber\(historico\.metadata\?\.total_registros_filtrados\?\?0\):[\"']—[\"']", fonte)
    assert re.search(r"nucleoDisponivel\?formatNumber\(abertos\.length\):[\"']—[\"']", fonte)
    assert re.search(r"window\.addEventListener\([\"']online[\"'],\s*aoReconectar\)", fonte)


def test_historico_explicita_que_e_somente_consulta():
    fonte = HISTORICO.read_text(encoding="utf-8")

    assert "SOMENTE CONSULTA · NÃO ALTERA O CRM" in fonte
    assert "Base histórica consolidada para consulta e auditoria." in fonte
    assert "HIST-006" not in fonte
    assert "HIST-007" not in fonte
    assert "READ-ONLY · NÃO PROMOVIDO" not in fonte
