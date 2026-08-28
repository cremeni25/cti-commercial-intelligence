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
    return isinstance(exc, TRANSIENT_HTTP_ERRORS)
