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


def metadados_so_pedidos():
    return {
        "fontes": [{"tipo": "CTI", "descricao": "Ferramentas internas autorizadas do CTI."}],
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_dominio_cti",
                "argumentos": {"dominio": "pedidos", "termo": "PED-001", "limite": 1},
                "resumo": {"erro": None, "dominio": "pedidos", "total_retornado": 1},
            }
        ],
        "evidencias_requeridas": ["pedidos"],
        "evidencias_atendidas": ["pedidos"],
    }


def test_pedido_nao_pode_provar_portfolio_atual_sem_catalogo():
    auditoria = construir_auditoria_evidencial(
        "(2) DADOS INTERNOS CTI\n- O modelo X4-7500 integra o portfólio atual do CTI.",
        metadados_so_pedidos(),
        "Analise o pedido PED-001.",
    )["auditoria_evidencial"]
    afirmacao = auditoria["afirmacoes"][0]
    assert afirmacao["fontes_evidencia"] == []
    assert afirmacao["status_rastreabilidade"] == "SEM_EVIDENCIA_EXPLICITA"
    assert auditoria["totais"]["afirmacoes_sem_evidencia_explicita"] == 1


def test_fonte_unica_de_pedidos_nao_substitui_vendas_ou_produtos():
    auditoria = construir_auditoria_evidencial(
        "(2) DADOS INTERNOS CTI\n- Há vendas recentes do modelo no portfólio atual.",
        metadados_so_pedidos(),
        "Analise o pedido PED-001.",
    )["auditoria_evidencial"]
    afirmacao = auditoria["afirmacoes"][0]
    assert afirmacao["fontes_evidencia"] == []
    assert afirmacao["status_rastreabilidade"] == "SEM_EVIDENCIA_EXPLICITA"


def test_portfolio_atual_continua_sem_evidencia_mesmo_quando_frase_tambem_cita_pedido():
    auditoria = construir_auditoria_evidencial(
        "(2) DADOS INTERNOS CTI\n- O portfólio atual da CTI inclui o modelo X4-7500 na linha Trailer, usado no pedido analisado.",
        metadados_so_pedidos(),
        "Analise o pedido PED-001.",
    )["auditoria_evidencial"]
    afirmacao = auditoria["afirmacoes"][0]
    assert afirmacao["fontes_evidencia"] == []
    assert afirmacao["status_rastreabilidade"] == "SEM_EVIDENCIA_EXPLICITA"


def test_portfolio_atual_usa_catalogo_quando_catalogo_foi_consultado():
    auditoria = construir_auditoria_evidencial(
        "(2) DADOS INTERNOS CTI\n- O portfólio atual da CTI inclui o modelo X4-7500 na linha Trailer, usado no pedido analisado.",
        metadados_multifonte(),
        "Compare mercado, portfólio e vendas.",
    )["auditoria_evidencial"]
    afirmacao = auditoria["afirmacoes"][0]
    assert afirmacao["fontes_evidencia"] == ["CTI_1"]
    assert afirmacao["status_rastreabilidade"] == "RASTREAVEL"


def test_inferencia_com_premissa_de_portfolio_nao_consultado_fica_base_parcial():
    auditoria = construir_auditoria_evidencial(
        "(3) CRUZAMENTO E IMPLICAÇÕES COMERCIAIS\n- O equipamento X4-7500 faz parte do portfólio atual da CTI e já teve vendas confirmadas, mostrando aderência ao mercado.",
        metadados_so_pedidos(),
        "Compare o pedido com o mercado.",
    )["auditoria_evidencial"]
    afirmacao = auditoria["afirmacoes"][0]
    assert afirmacao["tipo"] == "INFERENCIA_RECOMENDACAO"
    assert afirmacao["status_rastreabilidade"] == "BASE_PARCIAL"
    assert set(afirmacao["premissas_fatuais_nao_sustentadas"]) == {"produtos", "vendas"}
    assert auditoria["totais"]["inferencias_base_parcial"] == 1


def test_inferencia_com_premissas_consultadas_fica_rastreavel():
    auditoria = construir_auditoria_evidencial(
        "(3) CRUZAMENTO E IMPLICAÇÕES COMERCIAIS\n- O equipamento faz parte do portfólio atual e já teve vendas confirmadas; recomenda-se priorizar sua expansão.",
        metadados_multifonte(),
        "Compare mercado, portfólio e vendas.",
    )["auditoria_evidencial"]
    afirmacao = auditoria["afirmacoes"][0]
    assert afirmacao["status_rastreabilidade"] == "RASTREAVEL"
    assert afirmacao["premissas_fatuais_nao_sustentadas"] == []


def test_controle_ia006_publicado():
    resultado = construir_auditoria_evidencial("- Recomenda-se acompanhar o pedido.", {"fontes": [], "ferramentas": [], "evidencias_requeridas": [], "evidencias_atendidas": []}, "O que recomenda?")
    assert resultado["controle_auditoria_evidencial"] == "ia006_cadeia_afirmacao_evidencia_origem"
    assert resultado["auditoria_evidencial"]["versao"] == "IA-006-v1"
