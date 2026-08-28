from __future__ import annotations

import httpx

TRANSIENT_HTTP_ERRORS = (
    httpx.ReadError,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
)


def is_transient_http_error(exc: BaseException) -> bool:
    if isinstance(exc, TRANSIENT_HTTP_ERRORS):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return any(is_transient_http_error(item) for item in exc.exceptions)
    if exc.__cause__ is not None and is_transient_http_error(exc.__cause__):
        return True
    if exc.__context__ is not None and is_transient_http_error(exc.__context__):
        return True
    return False
