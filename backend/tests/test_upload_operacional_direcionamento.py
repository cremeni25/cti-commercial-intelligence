from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "upload" / "page.tsx"
SERVICE = ROOT / "frontend" / "src" / "services" / "cti-api.ts"


def test_importacao_unificada_substitui_direcionamento_manual():
    page = PAGE.read_text(encoding="utf-8")
    assert "Importar Dados" in page
    assert "Um único ponto de entrada" in page
    assert "O CTI identifica o tratamento correto" in page
    assert "pareceFunilComercial" not in page
    assert "Abrir Fontes & IA" not in page


def test_anfir_e_governanca_continuam_com_tratamentos_internos_separados():
    service = SERVICE.read_text(encoding="utf-8")
    assert "/upload/anfir/seguro" in service
    assert 'BACKOFFICE_URL = "/api/crm-proxy/backoffice-fontes"' in service
    assert "SEM_REGISTROS_PROCESSADOS" in service
