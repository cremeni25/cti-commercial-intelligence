import httpx

from core.transient_http import is_transient_http_error


def test_read_error_is_transient():
    assert is_transient_http_error(httpx.ReadError("temporary read failure"))


def test_nested_transient_error_is_detected():
    try:
        try:
            raise httpx.RemoteProtocolError("stream reset")
        except httpx.RemoteProtocolError as exc:
            raise RuntimeError("wrapper") from exc
    except RuntimeError as wrapped:
        assert is_transient_http_error(wrapped)


def test_business_error_is_not_transient():
    assert not is_transient_http_error(ValueError("invalid commercial data"))
