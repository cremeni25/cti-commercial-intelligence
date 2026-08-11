from services.ia_comercial_planejamento import requer_planejamento, validar_plano


def auditoria_base():
    return {
        "afirmacoes": [
            {
                "id": "A1",
                "tipo": "FATO_CTI",
                "texto": "O pedido PED-001 está na etapa PEDIDO e a próxima etapa é CARRIER.",
                "status_rastreabilidade": "RASTREAVEL",
            },
            {
                "id": "A2",
                "tipo": "FATO_CTI",
                "texto": "A oportunidade vinculada está em status GANHO.",
                "status_rastreabilidade": "RASTREAVEL",
            },
            {
                "id": "A3",
                "tipo": "INFERENCIA_RECOMENDACAO",
                "texto": "O portfólio atual pode exigir atualização.",
                "status_rastreabilidade": "BASE_PARCIAL",
                "premissas_fatuais_nao_sustentadas": ["produtos"],
            },
            {
                "id": "A4",
                "tipo": "FATO_CTI",
                "texto": "Há uma venda recente.",
                "status_rastreabilidade": "SEM_EVIDENCIA_EXPLICITA",
            },
        ]
    }


def test_detecta_intencao_de_planejamento():
    assert requer_planejamento("Qual a prioridade e o que devo fazer agora?") is True
    assert requer_planejamento("Qual é a etapa atual do pedido?") is False


def test_plano_remove_fundamento_sem_evidencia():
    plano = validar_plano(
        {
            "objetivo": "Resolver o pedido.",
            "acoes": [
                {
                    "acao": "Usar a venda recente como argumento.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A4"],
                }
            ],
        },
        auditoria_base(),
    )
    assert plano["acoes"] == []


def test_plano_nao_manda_avancar_oportunidade_ganha():
    plano = validar_plano(
        {
            "objetivo": "Organizar próximos passos.",
            "acoes": [
                {
                    "acao": "Avançar a oportunidade para a próxima etapa do pipeline.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A2"],
                },
                {
                    "acao": "Priorizar o envio do pedido à Carrier.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A1"],
                },
            ],
        },
        auditoria_base(),
    )
    assert len(plano["acoes"]) == 1
    assert "pedido" in plano["acoes"][0]["acao"].casefold()
    assert plano["oportunidade_encerrada_detectada"] is True


def test_base_parcial_e_propagada_para_acao():
    plano = validar_plano(
        {
            "objetivo": "Planejar evolução comercial.",
            "acoes": [
                {
                    "acao": "Avaliar atualização do portfólio.",
                    "prioridade": "MEDIA",
                    "horizonte": "MEDIO_PRAZO",
                    "fundamentos": ["A3"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["qualificacao_evidencial"] == "BASE_PARCIAL"
    assert acao["lacunas_evidenciais"] == ["produtos"]


def test_ordem_prioridade_e_horizonte_sao_normalizados():
    plano = validar_plano(
        {
            "objetivo": "Executar.",
            "acoes": [
                {
                    "ordem": 99,
                    "acao": "Enviar o pedido à Carrier.",
                    "prioridade": "URGENTE",
                    "horizonte": "AMANHA",
                    "fundamentos": ["A1"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["ordem"] == 1
    assert acao["prioridade"] == "MEDIA"
    assert acao["horizonte"] == "CURTO_PRAZO"
