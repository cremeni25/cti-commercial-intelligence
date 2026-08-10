from routers import ia_comercial_cti_router as router


def test_pergunta_sem_periodo_concreto_usa_historico_completo_como_universo_base():
    mensagem = (
        "Compare a linha Trailer no DDD 011 com os dados ANFIR disponíveis. "
        "Mostre o que o CTI indica sobre clientes, modelos e concentração territorial "
        "e diga onde existem sinais de oportunidade comercial."
    )

    assert router._periodo_temporal_explicito(mensagem) is False

    mensagem_agente, controle = router._mensagem_com_contexto_temporal(mensagem)

    assert controle == "sem_periodo_explicito_todo_historico"
    assert "TODO_HISTORICO" in mensagem_agente
    assert "não deriva de filtros" in mensagem_agente
    assert "outros módulos do CTI" in mensagem_agente


def test_periodo_concreto_pedido_pelo_usuario_e_preservado():
    mensagem = "Compare Trailer no DDD 011 nos últimos 90 dias com a ANFIR."

    assert router._periodo_temporal_explicito(mensagem) is True

    mensagem_agente, controle = router._mensagem_com_contexto_temporal(mensagem)

    assert controle == "periodo_explicito_usuario"
    assert "explicitamente definido pelo usuário" in mensagem_agente
    assert "não o substitua silenciosamente" in mensagem_agente
    assert "TODO_HISTORICO" not in mensagem_agente


def test_ano_e_intervalo_de_datas_sao_periodos_explicitos():
    assert router._periodo_temporal_explicito("Analise a ANFIR em 2025") is True
    assert router._periodo_temporal_explicito("Analise de 01/01/2025 a 31/12/2025") is True
    assert router._periodo_temporal_explicito("Analise de 2025-01-01 até 2025-12-31") is True


def test_termo_recente_sem_janela_concreta_nao_autoriza_inventar_90_dias():
    mensagem = "Quais são as movimentações recentes de Trailer no DDD 011?"

    assert router._periodo_temporal_explicito(mensagem) is False

    mensagem_agente, controle = router._mensagem_com_contexto_temporal(mensagem)
    assert controle == "sem_periodo_explicito_todo_historico"
    assert "Janelas recentes podem ser analisadas complementarmente" in mensagem_agente
