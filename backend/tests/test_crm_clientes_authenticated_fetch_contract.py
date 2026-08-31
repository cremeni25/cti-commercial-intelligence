from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLIENTES_PAGE = ROOT / "frontend" / "src" / "app" / "crm-app" / "clientes" / "page.tsx"


def test_carteira_clientes_usa_fetch_seguro_autenticado():
    source = CLIENTES_PAGE.read_text(encoding="utf-8")
    assert 'fetchCrmSeguroProxy("crm-seguro/clientes"' in source
    assert 'fetch("/api/crm-proxy/crm-seguro/clientes"' not in source


def test_nucleo_comercial_mantem_leitura_no_proxy_normal():
    source = CLIENTES_PAGE.read_text(encoding="utf-8")
    assert 'fetch("/api/crm-proxy/crm/nucleo-comercial"' in source
