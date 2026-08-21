from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "upload" / "page.tsx"
SERVICE = ROOT / "frontend" / "src" / "services" / "cti-api.ts"


def test_upload_operacional_explica_que_parser_e_anfir():
    page = PAGE.read_text(encoding="utf-8")
    assert "Upload Operacional ANFIR" in page
    assert "Funil de Vendas, Pipeline, Oportunidades e Histórico Comercial não entram neste parser ANFIR." in page
    assert 'window.location.href = "/backoffice-fontes"' in page
    assert "pareceFunilComercial" in page


def test_upload_anfir_continua_no_endpoint_canonico():
    service = SERVICE.read_text(encoding="utf-8")
    assert "/upload/anfir/seguro" in service
