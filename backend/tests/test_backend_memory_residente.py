import ast
import inspect
from pathlib import Path

from routers import engine_router, upload_router


def _imports_top_level(fonte: str) -> set[str]:
    arvore = ast.parse(fonte)
    imports: set[str] = set()
    for node in arvore.body:
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports


def test_engine_nao_carrega_pandas_no_bootstrap_da_rota():
    fonte = inspect.getsource(engine_router)
    imports = _imports_top_level(fonte)
    assert "engine.market_engine" not in imports
    assert "from engine.market_engine import MarketEngine" in fonte


def test_upload_nao_carrega_parser_pesado_no_bootstrap_da_rota():
    fonte = inspect.getsource(upload_router)
    imports = _imports_top_level(fonte)
    assert "parsers.viena_parser" not in imports
    assert "from parsers.viena_parser import processar_planilha_viena_com_relatorio as _processar" in fonte


def test_sitecustomize_limita_pools_e_instala_pandas_lazy():
    caminho = Path(__file__).resolve().parents[1] / "sitecustomize.py"
    fonte = caminho.read_text(encoding="utf-8")
    assert "OPENBLAS_NUM_THREADS" in fonte
    assert "OMP_NUM_THREADS" in fonte
    assert "MKL_NUM_THREADS" in fonte
    assert "NUMEXPR_NUM_THREADS" in fonte
    assert '_instalar_import_lazy("pandas")' in fonte
    assert "LazyLoader" in fonte
