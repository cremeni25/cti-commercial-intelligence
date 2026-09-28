from pathlib import Path


def test_tela_vendas_usa_fonte_segura_sem_nucleo_operacional():
    fonte = (Path(__file__).parents[2] / "frontend/src/app/vendas/page.tsx").read_text(encoding="utf-8")
    assert 'fetchCrmSeguroProxy("crm-seguro/vendas"' in fonte
    assert 'crm-seguro/nucleo-comercial' not in fonte
    assert 'pedidosPermitidos' not in fonte


def test_backend_vendas_seguras_governa_escopo():
    fonte = (Path(__file__).parents[1] / "routers/crm_scope_vendas_router.py").read_text(encoding="utf-8")
    assert '@router.get("/vendas")' in fonte
    assert '_venda_autorizada' in fonte
    assert 'listar_vendas()' in fonte
