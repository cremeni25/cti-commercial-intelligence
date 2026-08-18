"""Compatibilidade entre camadas históricas da IA e a leitura universal CTI."""

try:
    from . import ia_comercial_agente_crm as _crm

    if not hasattr(_crm, "_ORIGINAL_FONTES_REQUERIDAS"):
        _crm._ORIGINAL_FONTES_REQUERIDAS = _crm._fontes_requeridas_universais
    if not hasattr(_crm, "_fontes_requeridas_ia003"):
        _crm._fontes_requeridas_ia003 = _crm._fontes_requeridas_universais
    if not hasattr(_crm, "_necessita_web_autonoma"):
        _crm._necessita_web_autonoma = _crm._necessita_web
    if not hasattr(_crm, "_pede_cruzamento_cti_explicito"):
        _crm._pede_cruzamento_cti_explicito = lambda mensagem: not _crm._somente_web_explicito(mensagem)
    if not hasattr(_crm, "_ferramentas_agente_ia003"):
        _crm._ferramentas_agente_ia003 = _crm._ferramentas_universais
except Exception:
    pass

try:
    from . import ia_comercial_auditoria_proveniencia as _auditoria_proveniencia  # noqa: F401
except Exception:
    pass

# Ontologia e guard permanecem ativos antes da IA-010. Assim, a continuidade
# preserva as proteções homologadas e só substitui a antiga obrigatoriedade de CTI.
try:
    from . import ia_comercial_ontologia as _ontologia  # noqa: F401
except Exception:
    pass

try:
    from . import ia_comercial_guard_semantico as _guard_semantico  # noqa: F401
except Exception:
    pass

# IA-010 continuidade tem precedência final sobre roteamento de fontes:
# CTI condicional por relevância + memória semântica documental persistente.
try:
    from . import ia_comercial_ia010_continuidade as _ia010_continuidade  # noqa: F401
except Exception:
    pass

try:
    from . import ia_comercial_ia010_auditoria_patch as _ia010_auditoria_patch  # noqa: F401
except Exception:
    pass

try:
    from . import ia_comercial_artefatos_patch as _artefatos_patch  # noqa: F401
except Exception:
    pass

try:
    from . import ia_comercial_artefatos_pos_sintese as _artefatos_pos_sintese  # noqa: F401
except Exception:
    pass
