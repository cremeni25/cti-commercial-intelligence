from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def test_middleware_asgi_nao_repete_call_next():
    source = MAIN.read_text(encoding="utf-8")
    trecho = source.split('@app.middleware("http")', 1)[1].split("app.add_middleware(", 1)[0]
    assert trecho.count("call_next(request)") == 1
    assert "asyncio.sleep" not in trecho
    assert "for indice" not in trecho
    assert "ClosedResourceError" in trecho


def test_main_nao_importa_retry_http_para_reexecutar_request_asgi():
    source = MAIN.read_text(encoding="utf-8")
    assert "from core.transient_http import is_transient_http_error" not in source
