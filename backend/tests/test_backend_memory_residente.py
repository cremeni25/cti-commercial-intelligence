import inspect
from pathlib import Path

from routers import engine_router, upload_router


def test_engine_nao_carrega_pandas_no_bootstrap_da_rota():
    fonte = inspect.getsource(engine_router)
    antes_endpoint = fonte.split('def market_intelligence', 1)[0]
    assert 'from engine.market_engine import MarketEngine' not in antes_endpoint
    assert 'from engine.market_engine import MarketEngine' in fonte


def test_upload_nao_carrega_parser_pesado_no_bootstrap_da_rota():
    fonte = inspect.getsource(upload_router)
    antes_endpoint = fonte.split('def upload_anfir_seguro', 1)[0]
    assert 'from parsers.viena_parser import processar_planilha_viena_com_relatorio' not in antes_endpoint
    assert 'from parsers.viena_parser import processar_planilha_viena_com_relatorio' in fonte


def test_sitecustomize_limita_pools_e_instala_pandas_lazy():
    caminho = Path(__file__).resolve().parents[1] / 'sitecustomize.py'
    fonte = caminho.read_text(encoding='utf-8')
    assert 'OPENBLAS_NUM_THREADS' in fonte
    assert 'OMP_NUM_THREADS' in fonte
    assert 'MKL_NUM_THREADS' in fonte
    assert 'NUMEXPR_NUM_THREADS' in fonte
    assert '_instalar_import_lazy("pandas")' in fonte
    assert 'LazyLoader' in fonte
