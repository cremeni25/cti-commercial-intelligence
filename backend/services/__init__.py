"""Compatibilidade entre camadas históricas da IA e a leitura universal CTI."""

# A arquitetura universal substituiu o roteamento por palavras-chave, mas camadas
# IA-006/IA-007 ainda importam aliases internos antigos. Mantemos esses aliases
# apontando para a nova política universal, sem reativar o comportamento legado.
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

# IA-010 continuidade: CTI condicional + memória semântica documental persistente.
try:
    from . import ia_comercial_ia010_continuidade as _ia010_continuidade  # noqa: F401
except Exception:
    pass

# IA-010 residual: corrige transições WEB -> ANEXO -> INFERÊNCIA e registra
# memória semântica como origem documental rastreável.
try:
    from . import ia_comercial_ia010_auditoria_patch as _ia010_auditoria_patch  # noqa: F401
except Exception:
    pass

try:
    from . import ia_comercial_ontologia as _ontologia  # noqa: F401
except Exception:
    pass

try:
    from . import ia_comercial_guard_semantico as _guard_semantico  # noqa: F401
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
