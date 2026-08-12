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
    # O pacote services também é usado por módulos que não carregam a IA.
    # Falhas de importação reais continuam sendo reveladas quando a IA é importada.
    pass
