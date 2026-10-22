"""Authentication boundary for legacy and current application routes alike."""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool
from core.admin_auth import usuario_atual

# Public onboarding and independently signed document previews retain their
# existing validation. Commercial data never becomes public by omitting a token.
PUBLIC = {
    ("GET", "/"), ("GET", "/status"), ("GET", "/health"),
    ("GET", "/auth/bootstrap/status"), ("POST", "/auth/bootstrap"),
    ("POST", "/auth/access-requests"), ("GET", "/auth/access-requests/health"),
    ("GET", "/docs"), ("GET", "/openapi.json"), ("GET", "/redoc"),
}

async def application_access(request: Request, call_next):
    path = request.url.path.rstrip("/") or "/"
    if request.method == "OPTIONS" or (request.method, path) in PUBLIC or (
        request.method == "GET" and path.startswith("/documentos-preview/")
    ):
        return await call_next(request)
    authorization = request.headers.get("authorization", "").split(" ", 1)
    credentials = None
    if len(authorization) == 2:
        credentials = HTTPAuthorizationCredentials(scheme=authorization[0], credentials=authorization[1])
    try:
        request.state.cti_usuario = await run_in_threadpool(usuario_atual, credentials, request)
    except HTTPException as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response
