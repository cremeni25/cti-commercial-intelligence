from routers import crm_scope_mapa_insights_router as insights


def test_decisao_prioritaria_permanece_no_cliente_escolhido():
    direcionamento = {
        "texto": "Quem deve agir / para quem: MÔNICA → CLIENTE ALVO",
        "alvos": [
            {
                "responsavel": "MÔNICA",
                "cliente": "CLIENTE ALVO",
                "unidades": 5,
                "ocorrencias": 5,
                "linha_principal": "Direct Drive",
            }
        ],
    }
    anfir = [
        {
            "ano": 2026,
            "mes": 9,
            "cliente": "CLIENTE ALVO",
            "linha": "DD",
            "quantidade": 5,
            "status": "TK",
        }
    ]

    enriquecido = insights._enriquecer_direcionamento(
        direcionamento,
        anfir,
        historico=[],
        crm=[],
        contexto_leitura="No consolidado, a maior concentração de perdas está em Direct Drive.",
    )
    leitura, acao = insights._aplicar_decisao_prioritaria(
        enriquecido,
        "leitura agregada",
        "ação agregada",
    )

    assert leitura.startswith("CLIENTE ALVO concentra 5 unidade(s) em 5 ocorrência(s) ANFIR 2026")
    assert "sem cobertura comercial registrada" in leitura
    assert "lacuna de evidência" in leitura
    assert "Contexto do ranking:" in leitura
    assert acao.startswith("MÔNICA: qualificar CLIENTE ALVO")
    assert "registrar a interação no CRM" in acao
    assert enriquecido["alvos"][0]["concorrencia"] == "TK"


def test_decisao_com_crm_ativo_muda_de_cobertura_para_avanco():
    direcionamento = {
        "texto": "Prioridade de acompanhamento: RESPONSÁVEL → CLIENTE CRM",
        "alvos": [
            {
                "responsavel": "RESPONSÁVEL",
                "cliente": "CLIENTE CRM",
                "unidades": 3,
                "ocorrencias": 2,
                "linha_principal": "Trailer",
            }
        ],
    }
    anfir = [
        {"ano": 2026, "mes": 8, "cliente": "CLIENTE CRM", "linha": "TR", "quantidade": 3, "status": "Carrier"}
    ]
    crm = [
        {"cliente": "CLIENTE CRM", "status": "ABERTO", "valor_estimado": 100000, "created_at": "2026-09-01"}
    ]

    enriquecido = insights._enriquecer_direcionamento(
        direcionamento,
        anfir,
        historico=[],
        crm=crm,
        contexto_leitura="Contexto agregado preservado.",
    )
    leitura, acao = insights._aplicar_decisao_prioritaria(enriquecido, "agregado", "agregada")

    assert "Há 1 negócio(s) ativo(s) no CRM" in leitura
    assert acao.startswith("RESPONSÁVEL: avançar o negócio ativo de CLIENTE CRM")
    assert enriquecido["alvos"][0]["cobertura"] == "CRM_ATIVO"
