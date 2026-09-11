def pytest_runtest_setup(item):
    """Mantém doubles de consulta legados compatíveis com a API Supabase usada em produção."""
    query = getattr(item.module, "Query", None)
    if query is not None and not hasattr(query, "limit"):
        setattr(query, "limit", lambda self, *_args, **_kwargs: self)
