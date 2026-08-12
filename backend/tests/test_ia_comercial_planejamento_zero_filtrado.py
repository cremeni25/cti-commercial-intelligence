from services.ia_comercial_planejamento import validar_plano


def auditoria_zero_filtrado_oportunidades():
    return {
        "afirmacoes": [
            {
                "id": "A1",
                "tipo": "FATO_CTI",
                "texto": "O pedido PED-20260804-A24FA6A7 está na etapa PEDIDO e a próxima etapa é CARRIER.",
                "status_rastreabilidade": "RASTREAVEL",
            },
            {
                "id": "A2",
                "tipo": "FATO_CTI",
                "texto": "A oportunidade vinculada ao pedido está em status GANHO.",
                "status_rastreabilidade": "RASTREAVEL",
            },
            {
                "id": "A3",
                "tipo": "FATO_CTI",
                "texto": "Não há oportunidades comerciais ativas vinculadas ao pedido além da citada.",
                "status_rastreabilidade": "RASTREAVEL",
            },
        ],
        "evidencias_atendidas": ["pedidos", "oportunidades"],
        "origens_execucao": [
            {
                "id": "CTI_1",
                "tipo": "CTI",
                "dominio": "pedidos",
                "filtros": {"termo": "PED-20260804-A24FA6A7"},
                "total_retornado": 1,
            },
            {
                "id": "CTI_2",
                "tipo": "CTI",
                "dominio": "oportunidades",
                "filtros": {"termo": "PED-20260804-A24FA6A7"},
                "total_retornado": 0,
            },
        ],
    }


def test_zero_filtrado_nao_pode_fundamentar_ausencia_de_oportunidade():
    plano = validar_plano(
        {
            "objetivo": "Conduzir o pedido.",
            "acoes": [
                {
                    "acao": "Como não há oportunidades vinculadas, encerrar qualquer acompanhamento de pipeline.",
                    "prioridade": "MEDIA",
                    "horizonte": "CURTO_PRAZO",
                    "fundamentos": ["A3"],
                },
                {
                    "acao": "Enviar o pedido à Carrier e acompanhar o ciclo operacional.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A1"],
                },
            ],
        },
        auditoria_zero_filtrado_oportunidades(),
    )

    assert len(plano["acoes"]) == 1
    assert "Carrier" in plano["acoes"][0]["acao"]


def test_oportunidade_ganha_continua_detectada_sem_usar_falso_negativo():
    plano = validar_plano(
        {
            "objetivo": "Conduzir o pedido.",
            "acoes": [
                {
                    "acao": "Avançar a oportunidade para a próxima etapa do pipeline.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A2"],
                },
                {
                    "acao": "Acompanhar o pedido após o envio à Carrier.",
                    "prioridade": "MEDIA",
                    "horizonte": "CURTO_PRAZO",
                    "fundamentos": ["A1"],
                },
            ],
        },
        auditoria_zero_filtrado_oportunidades(),
    )

    assert plano["oportunidade_encerrada_detectada"] is True
    assert len(plano["acoes"]) == 1
    assert "pedido" in plano["acoes"][0]["acao"].casefold()
