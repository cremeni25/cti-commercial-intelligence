import inspect

from routers import backoffice_fontes_router, upload_router


def test_upload_operacional_publica_contrato_canonico_no_relatorio():
    fonte = inspect.getsource(upload_router.upload_anfir_seguro)
    assert "contrato_upload_operacional" in fonte
    assert 'relatorio["ingestao_canonica"]' in fonte


def test_backoffice_persiste_contrato_canonico_na_proveniencia():
    fonte = inspect.getsource(backoffice_fontes_router.receber_fonte)
    assert "contrato_backoffice_fontes" in fonte
    assert '"ingestao_canonica": contrato_ingestao' in fonte
