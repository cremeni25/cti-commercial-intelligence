from __future__ import annotations

from services import ia_comercial_agente_crm as crm
from services.ia_comercial_sintese_crm import sintetizar_fatos_execucao


def test_web_explicita_soma_web_ao_universo_cti_por_padrao():
    pergunta = "entre os dados contidos no cti e através de pesquisa na web, relacione as 05 maiores implementadoras do Brasil"

    assert crm._necessita_web(pergunta) is True
    assert crm._fontes_requeridas_universais(pergunta) == {"universo_cti", "web"}


def test_web_so_fica_pura_quando_usuario_exclui_cti_explicitamente():
    pergunta = "Pesquise somente na web as novidades recentes da Thermo King; não use o CTI."

    assert crm._somente_web_explicito(pergunta) is True
    assert crm._fontes_requeridas_universais(pergunta) == {"web"}


def test_pergunta_interna_nao_depende_de_vocabulario_de_dominio():
    perguntas = [
        "Quem aparece mais vezes na nossa base?",
        "Quais empresas concentram mais registros?",
        "Me mostre onde está a maior concentração comercial.",
        "Quais são as maiores implementadoras do Brasil?",
        "Qual cliente comprou mais?",
    ]

    for pergunta in perguntas:
        assert "universo_cti" in crm._fontes_requeridas_universais(pergunta)


def test_execucao_web_pura_expoe_fisicamente_apenas_web_search():
    token = crm._EXECUCAO_WEB_PURA.set(True)
    try:
        ferramentas = crm._ferramentas_universais()
    finally:
        crm._EXECUCAO_WEB_PURA.reset(token)

    assert ferramentas
    assert all(item.get("type") == "web_search" for item in ferramentas)


def test_execucao_cti_expoe_catalogo_consulta_universal_e_web():
    token = crm._EXECUCAO_WEB_PURA.set(False)
    try:
        ferramentas = crm._ferramentas_universais()
    finally:
        crm._EXECUCAO_WEB_PURA.reset(token)

    nomes = {item.get("name") for item in ferramentas if item.get("type") == "function"}
    assert nomes == {"catalogar_universo_cti", "consultar_universo_cti"}
    assert any(item.get("type") == "web_search" for item in ferramentas)


def test_sintese_web_preserva_resposta_do_agente_e_registra_urls():
    metadados = {
        "evidencias_atendidas": ["web"],
        "fontes": [
            {"tipo": "WEB", "descricao": "Fonte A", "url": "https://example.com/a"},
            {"tipo": "WEB", "descricao": "Fonte B", "url": "https://example.com/b"},
        ],
    }
    texto, controle = sintetizar_fatos_execucao(
        "Quais são as novidades mais recentes da Thermo King?",
        metadados,
        "usuario",
        "ADMIN_MASTER",
    )
    assert texto is None
    assert controle["controle_web_proveniencia"] == "fontes_url_execucao_atual"
    assert controle["web_fontes_sintese"] == 2
