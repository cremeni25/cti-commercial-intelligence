from services.ia_comercial_auditoria_evidencial import construir_auditoria_evidencial


def metadados_multifonte():
    return {
        "fontes": [{"tipo": "WEB", "descricao": "Fonte mercado", "url": "https://example.com/mercado"}],
        "ferramentas": [
            {"tipo": "CTI", "ferramenta": "consultar_catalogo_produtos_cti", "argumentos": {"termo": None}, "resumo": {"erro": None}},
            {"tipo": "CTI", "ferramenta": "consultar_dominio_cti", "argumentos": {"dominio": "vendas", "termo": None, "limite": 100, "offset": 0, "status": None}, "resumo": {"erro": None, "dominio": "vendas", "total_retornado": 3}},
        ],
        "evidencias_requeridas": ["web", "produtos", "vendas"],
        "evidencias_atendidas": ["web", "produtos", "vendas", "relacionamentos_vendas"],
        "controle_temporal_pergunta": "sem_periodo_explicito_todo_historico",
        "controle_recorte_base": "restricoes_explicitas_pergunta",
    }


def test_origens_web_e_cti_preservam_filtros_reais():
    auditoria = construir_auditoria_evidencial(
        "(1) FATOS EXTERNOS VERIFICADOS\n- O mercado apresenta inovação.\n(2) DADOS INTERNOS CTI\n- O portfólio tem modelos ativos.\n- Há três vendas registradas.",
        metadados_multifonte(),
        "Compare mercado, portfólio e vendas.",
    )["auditoria_evidencial"]
    assert auditoria["historico_conta_como_evidencia"] is False
    assert len(auditoria["origens_execucao"]) == 3
    venda = next(o for o in auditoria["origens_execucao"] if o.get("dominio") == "vendas")
    assert venda["filtros"]["termo"] is None
    assert venda["filtros"]["limite"] == 100
    assert venda["total_retornado"] == 3


def test_afirmacoes_multifonte_ligam_origens_compativeis():
    auditoria = construir_auditoria_evidencial(
        "(1) FATOS EXTERNOS VERIFICADOS\n- O mercado apresenta inovação recente.\n(2) DADOS INTERNOS CTI\n- O portfólio inclui modelos ativos.\n- Existem três vendas registradas.\n(3) CRUZAMENTO E IMPLICAÇÕES COMERCIAIS\n- Recomenda-se priorizar os modelos aderentes.",
        metadados_multifonte(),
        "Compare mercado, portfólio e vendas.",
    )["auditoria_evidencial"]
    fatos_web = [a for a in auditoria["afirmacoes"] if a["tipo"] == "FATO_WEB"]
    fatos_cti = [a for a in auditoria["afirmacoes"] if a["tipo"] == "FATO_CTI"]
    inferencias = [a for a in auditoria["afirmacoes"] if a["tipo"] == "INFERENCIA_RECOMENDACAO"]
    assert fatos_web and all(a["fontes_evidencia"] == ["WEB_1"] for a in fatos_web)
    assert any("CTI_1" in a["fontes_evidencia"] for a in fatos_cti if "portfólio" in a["texto"])
    assert any("CTI_2" in a["fontes_evidencia"] for a in fatos_cti if "vendas" in a["texto"])
    assert inferencias and set(inferencias[0]["derivada_de"]) == {"CTI_1", "CTI_2", "WEB_1"}


def test_evidencia_requerida_nao_atendida_fica_explicita():
    metadados = metadados_multifonte()
    metadados["evidencias_atendidas"] = ["web", "produtos"]
    resultado = construir_auditoria_evidencial("- Há novidade de mercado.", metadados, "Compare mercado, portfólio e vendas.")
    assert resultado["auditoria_evidencias_faltantes"] == ["vendas"]


def test_resposta_cti_de_fonte_unica_fica_rastreavel():
    metadados = {
        "fontes": [{"tipo": "CTI", "descricao": "Ferramentas internas autorizadas do CTI."}],
        "ferramentas": [{"tipo": "CTI", "ferramenta": "consultar_dominio_cti", "argumentos": {"dominio": "pedidos", "termo": "PED-001", "limite": 1}, "resumo": {"erro": None, "dominio": "pedidos", "total_retornado": 1}}],
        "evidencias_requeridas": ["pedidos"],
        "evidencias_atendidas": ["pedidos"],
    }
    auditoria = construir_auditoria_evidencial("O pedido PED-001 está na etapa PEDIDO.\n- Próxima etapa: CARRIER.", metadados, "Analise o pedido PED-001.")["auditoria_evidencial"]
    assert all(a["fontes_evidencia"] == ["CTI_1"] for a in auditoria["afirmacoes"])
    assert auditoria["totais"]["afirmacoes_sem_evidencia_explicita"] == 0


def test_controle_ia006_publicado():
    resultado = construir_auditoria_evidencial("- Recomenda-se acompanhar o pedido.", {"fontes": [], "ferramentas": [], "evidencias_requeridas": [], "evidencias_atendidas": []}, "O que recomenda?")
    assert resultado["controle_auditoria_evidencial"] == "ia006_cadeia_afirmacao_evidencia_origem"
    assert resultado["auditoria_evidencial"]["versao"] == "IA-006-v1"
