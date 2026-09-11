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
