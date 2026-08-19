from core.ingestion_reconciliation import pode_aprovar, preparar_plano


def test_comercial_vira_plano_sem_promocao_automatica():
    plano = preparar_plano(
        "COMERCIAL",
        [{"indice": 1, "dados": {"CNPJ": "12.345.678/0001-90", "Cliente": "Empresa A"}}],
    )
    assert plano["dominio_alvo"] == "CRM_COMERCIAL"
    assert plano["promocao_operacional_automatica"] is False
    assert plano["total_itens"] == 1
    assert plano["total_conflitos"] == 0
    assert plano["itens"][0]["entidade_sugerida"] == "CLIENTE"
    assert plano["itens"][0]["status_item"] == "VALIDO"


def test_anfir_vira_dominio_anfir_e_exige_gate():
    plano = preparar_plano(
        "MERCADO_ANFIR",
        [{"indice": 2, "dados": {"chassi": "ABC123", "implementadora": "FACCHINI", "modelo": "X"}}],
    )
    assert plano["dominio_alvo"] == "CTI_ANFIR"
    assert pode_aprovar(plano) is True
    assert plano["pronto_promocao"] is False


def test_registro_sem_dados_permanece_em_conflito():
    plano = preparar_plano("COMERCIAL", [{"indice": 3, "dados": {}}])
    assert plano["total_conflitos"] == 1
    assert plano["itens"][0]["acao_sugerida"] == "REVISAR"
    assert pode_aprovar(plano) is False


def test_classificacao_nao_operacional_nao_pode_preparar_plano():
    try:
        preparar_plano("TECNICO_PRODUTO", [{"indice": 1, "dados": {"modelo": "X"}}])
    except ValueError as exc:
        assert "não elegível" in str(exc)
    else:
        raise AssertionError("Era esperado bloqueio para conhecimento semântico.")
