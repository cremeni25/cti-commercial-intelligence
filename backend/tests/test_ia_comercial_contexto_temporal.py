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


def test_recorte_base_nao_pode_ganhar_fabricante_ou_outro_filtro_por_inferencia():
    mensagem = (
        "Compare a linha Trailer no DDD 011 com os dados ANFIR disponíveis e mostre clientes, "
        "modelos e concentração territorial."
    )

    mensagem_agente, _ = router._mensagem_com_contexto_temporal(mensagem)

    assert "somente dimensões explicitamente informadas na pergunta" in mensagem_agente
    assert "Não acrescente fabricante" in mensagem_agente
    assert "Recortes exploratórios adicionais" in mensagem_agente
    assert "não podem" not in mensagem.lower() or "fabricante" not in mensagem.lower()


def test_catalogo_nao_prova_modelo_no_historico_anfir():
    mensagem = "Quais modelos aparecem na linha Trailer no DDD 011 segundo os dados ANFIR disponíveis?"

    mensagem_agente, _ = router._mensagem_com_contexto_temporal(mensagem)

    assert "catálogo oficial informa portfólio/modelos disponíveis" in mensagem_agente
    assert "não prova que um modelo aparece no histórico ANFIR" in mensagem_agente
    assert "só atribua modelo ao histórico" in mensagem_agente


def test_clientes_globais_do_crm_nao_viram_clientes_do_recorte_sem_vinculo():
    mensagem = "Quais clientes aparecem no DDD 011 para Trailer segundo a ANFIR?"

    mensagem_agente, _ = router._mensagem_com_contexto_temporal(mensagem)

    assert "clientes do CRM podem servir como contexto" in mensagem_agente
    assert "sem vínculo territorial explícito" in mensagem_agente


def test_fabricante_explicito_continua_presente_na_pergunta_e_pode_integrar_o_recorte():
    mensagem = "Compare Trailer da Carrier no DDD 011 segundo a ANFIR."

    mensagem_agente, _ = router._mensagem_com_contexto_temporal(mensagem)

    assert mensagem in mensagem_agente
    assert "somente dimensões explicitamente informadas na pergunta" in mensagem_agente


def test_precisao_factual_nao_transforma_ausencia_em_confirmacao():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal("Analise os clientes do DDD 011.")

    assert "não transforme ausência de dado em confirmação" in mensagem_agente
    assert "vazio, nulo ou ausente" in mensagem_agente
    assert "não atribua categoria, status ou fato não registrado" in mensagem_agente


def test_maioria_e_predominancia_exigem_mais_de_cinquenta_por_cento():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal("Analise a distribuição de status.")

    assert "'maioria', 'predominante', 'líder', 'principal'" in mensagem_agente
    assert "estritamente mais de 50%" in mensagem_agente
    assert "sem maioria absoluta" in mensagem_agente


def test_cobertura_parcial_nao_vira_predominancia_do_universo():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal("Analise fabricantes no recorte.")

    assert "cobertura do campo for parcial" in mensagem_agente
    assert "entre os registros preenchidos" in mensagem_agente
    assert "não transforme a categoria mais frequente entre preenchidos em predominância do universo" in mensagem_agente


def test_status_operacional_nao_vira_venda_sem_semantica_explicita():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal("Analise os registros operacionais.")

    assert "Não converta status operacional" in mensagem_agente
    assert "em venda, negócio realizado" in mensagem_agente
    assert "sem semântica explícita da fonte" in mensagem_agente


def test_cliente_ativo_exige_status_explicito():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal("Quais clientes devo priorizar?")

    assert "Só qualifique cliente como ativo/inativo" in mensagem_agente
    assert "explicitamente preenchido na fonte" in mensagem_agente


def test_cobertura_de_campo_deve_ser_exata():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal("Analise a cobertura dos modelos.")

    assert "use contagens exatas" in mensagem_agente
    assert "todos os registros do recorte estão sem modelo" in mensagem_agente
    assert "não 'na maioria dos casos'" in mensagem_agente


def test_ia002_isola_execucao_factual_de_todo_historico_anterior():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal(
        "Compare Trailer no DDD 011 com a ANFIR."
    )

    assert "nesta etapa IA-002, a execução factual é isolada de todo histórico anterior da conversa" in mensagem_agente
    assert "fonte efetivamente consultada nesta execução" in mensagem_agente


def test_pipeline_nao_pode_ser_afirmado_sem_fonte_de_oportunidades_na_execucao():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal(
        "Compare Trailer no DDD 011 com a ANFIR."
    )

    assert "Não afirme pipeline, oportunidades ou seus status sem" in mensagem_agente
    assert "consultar a fonte de oportunidades nesta execução" in mensagem_agente


def test_catalogo_nao_pode_ser_afirmado_sem_consulta_atual():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal(
        "Compare Trailer no DDD 011 com a ANFIR."
    )

    assert "não nomeie modelos disponíveis do portfólio sem consultar o catálogo" in mensagem_agente


def test_vendas_nao_podem_ser_afirmadas_sem_consulta_atual():
    mensagem_agente, _ = router._mensagem_com_contexto_temporal(
        "Compare Trailer no DDD 011 com a ANFIR."
    )

    assert "não afirme vendas ou vínculos de venda sem consultar vendas" in mensagem_agente
    assert "não foi verificado nesta execução" in mensagem_agente
