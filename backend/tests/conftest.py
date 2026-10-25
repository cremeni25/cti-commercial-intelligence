def pytest_runtest_setup(item):
    """Mantém doubles de consulta legados compatíveis com a API Supabase usada em produção."""
    query = getattr(item.module, "Query", None)
    if query is None:
        return
    if not hasattr(query, "limit"):
        setattr(query, "limit", lambda self, *_args, **_kwargs: self)
    if not hasattr(query, "is_"):
        def _is(self, field, value):
            esperado = None if str(value).lower() == "null" else value
            self.filters.append((field, esperado))
            return self
        setattr(query, "is_", _is)


import pytest


@pytest.fixture(autouse=True)
def bloquear_transporte_supabase_real(monkeypatch):
    """Testes nunca acessam bancos remotos por uma consulta não simulada.

    TestClient e MockTransport continuam usando seus próprios transportes.
    Falha imediata evita retentativas longas e protege dados operacionais.
    """
    import httpx

    original = httpx.HTTPTransport.handle_request

    def enviar(transport, request):
        host = request.url.host
        if host.endswith((".supabase.co", ".supabase.in")):
            raise RuntimeError("Consulta Supabase remota bloqueada no teste; simule o transporte explicitamente.")
        return original(transport, request)

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", enviar)


@pytest.fixture
def legacy_authenticated_client(monkeypatch):
    """Legacy business-rule unit tests run as internal staff.

    HTTP authentication/denial tests use their own client and never opt into
    this fixture. No default authentication bypass is installed for the suite.
    """
    from core import application_access
    from core.admin_auth import UsuarioAutenticado
    usuario = UsuarioAutenticado(id="user-1", auth_id="auth-test", email="unit@example.invalid",
        nome="Internal test", tipo_usuario="ADMIN_MASTER", permissoes={"acesso_total": True})
    monkeypatch.setattr(application_access, "usuario_atual", lambda *_: usuario)
