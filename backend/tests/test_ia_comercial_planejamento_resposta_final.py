from routers.ia_comercial_cti_router import _renderizar_plano_validado


def test_renderiza_somente_acoes_validadas_do_plano():
    metadados = {
        "planejamento_comercial_ativo": True,
        "plano_comercial": {
            "objetivo": "Conduzir o pedido corretamente.",
            "acoes": [
                {
                    "ordem": 1,
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "acao": "Enviar o pedido à Carrier e registrar o protocolo.",
                    "fundamentos": ["A3", "A4"],
                    "qualificacao_evidencial": "EVIDENCIA_COMPLETA",
                    "dependencias": [],
                    "riscos": ["Atraso operacional."],
                    "resultado_esperado": "Avanço para CARRIER.",
                    "lacunas_evidenciais": [],
                }
            ],
        },
    }

    texto = _renderizar_plano_validado(metadados)

    assert texto is not None
    assert texto.startswith("PLANO COMERCIAL ESTRUTURADO")
    assert "Enviar o pedido à Carrier" in texto
    assert "A3, A4" in texto
    assert "EVIDENCIA_COMPLETA" in texto


def test_nao_renderiza_plano_inativo_ou_sem_acoes():
    assert _renderizar_plano_validado({"planejamento_comercial_ativo": False}) is None
    assert _renderizar_plano_validado({"planejamento_comercial_ativo": True, "plano_comercial": {"acoes": []}}) is None
