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

# A auditoria IA-006 histórica classifica a proveniência por seções formais. A
# leitura universal pode responder em prosa contínua; carregamos uma correção que
# preserva a API existente e evita atribuir fatos web ao CTI por coincidência de
# entidade ou pela existência de uma única consulta interna.
try:
    from . import ia_comercial_auditoria_proveniencia as _auditoria_proveniencia  # noqa: F401
except Exception:
    pass

# A ontologia comercial é carregada por último para envolver a leitura universal
# já montada: fixa o significado das entidades do CTI, declara a finalidade
# analítica das fontes e obriga a web a preservar o mesmo contexto comercial.
try:
    from . import ia_comercial_ontologia as _ontologia  # noqa: F401
except Exception:
    pass

# Guard final: se uma execução ainda tentar produzir ranking com fonte cadastral
# ou derivar a web para outro setor, refaz a investigação uma vez e bloqueia a
# resposta caso a ontologia continue inconsistente.
try:
    from . import ia_comercial_guard_semantico as _guard_semantico  # noqa: F401
except Exception:
    pass

# IA-009: a geração de gráfico/relatório/PDF é uma camada pós-síntese. Ela recebe
# apenas respostas e evidências já autorizadas, produz especificações determinísticas
# e não amplia permissões do agente, SQL ou ações comerciais.
try:
    from . import ia_comercial_artefatos_patch as _artefatos_patch  # noqa: F401
except Exception:
    pass
