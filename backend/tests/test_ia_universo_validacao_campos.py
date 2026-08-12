from services import ia_comercial_universo as universo


def test_validar_plano_rejeita_campo_inexistente_em_agrupamento():
    registros = [{"id": "1", "nome": "A"}, {"id": "2", "nome": "B"}]
    erro = universo._validar_plano_campos(
        registros,
        filtros=[],
        agrupar_por=["nome_implementadora"],
        metricas=[{"operacao": "count", "campo": None, "alias": "total"}],
        ordenar_por="total",
    )
    assert erro is not None
    assert "nome_implementadora" in erro["campos_invalidos"]
    assert "nome" in erro["campos_disponiveis"]


def test_validar_plano_permite_alias_de_metrica_na_ordenacao():
    registros = [{"implementadora": "A"}, {"implementadora": "B"}]
    erro = universo._validar_plano_campos(
        registros,
        filtros=[],
        agrupar_por=["implementadora"],
        metricas=[{"operacao": "count", "campo": None, "alias": "total_registros"}],
        ordenar_por="total_registros",
    )
    assert erro is None


def test_descricoes_distinguem_cadastro_de_historico():
    assert "histórico" in universo.FONTES_PUBLICAS["historico_anfir"].casefold()
    descricao_cadastro = universo.FONTES_PUBLICAS["implementadoras_cadastro"].casefold()
    assert "cadastro" in descricao_cadastro
    assert "não usar" in descricao_cadastro or "não é" in descricao_cadastro
