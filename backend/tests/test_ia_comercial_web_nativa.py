from __future__ import annotations

from services.ia_comercial_agente_crm import (
    _EXECUCAO_WEB_PURA,
    _ferramentas_agente_ia003,
    _fontes_requeridas_ia003,
    _necessita_web_autonoma,
    _pede_cruzamento_cti_explicito,
)
from services.ia_comercial_sintese_crm import sintetizar_fatos_execucao


def test_web_e_exigida_sem_comando_explicito_quando_fato_externo_e_atual():
    pergunta = (
        "Quais são as novidades mais recentes da Thermo King para refrigeração de transporte "
        "no Brasil e o que isso pode significar comercialmente para a operação Carrier/Viena?"
    )
    assert _necessita_web_autonoma(pergunta) is True
    assert _fontes_requeridas_ia003(pergunta) == {"web"}


def test_pergunta_externa_de_mercado_nao_abre_produtos_vendas_ou_anfir_por_vocabulario_generico():
    pergunta = (
        "Quais foram as principais novidades recentes no mercado brasileiro de transporte refrigerado "
        "e que impactos comerciais elas podem ter para a venda de equipamentos de refrigeração para transporte?"
    )
    assert _necessita_web_autonoma(pergunta) is True
    assert _pede_cruzamento_cti_explicito(pergunta) is False
    assert _fontes_requeridas_ia003(pergunta) == {"web"}


def test_execucao_web_pura_expoe_fisicamente_apenas_web_search():
    token = _EXECUCAO_WEB_PURA.set(True)
    try:
        ferramentas = _ferramentas_agente_ia003()
    finally:
        _EXECUCAO_WEB_PURA.reset(token)
    assert ferramentas
    assert all(item.get("type") == "web_search" for item in ferramentas)
    assert not any(item.get("type") == "function" for item in ferramentas)


def test_cruzamento_web_com_dados_internos_so_ocorre_quando_usuario_pede_explicitamente():
    pergunta = (
        "Quais são as novidades recentes do mercado de transporte refrigerado e como elas se comparam "
        "com nosso portfólio e nossas vendas no CTI?"
    )
    requeridas = _fontes_requeridas_ia003(pergunta)
    assert _necessita_web_autonoma(pergunta) is True
    assert _pede_cruzamento_cti_explicito(pergunta) is True
    assert "web" in requeridas
    assert "produtos" in requeridas
    assert "vendas" in requeridas


def test_pergunta_atual_do_crm_nao_aciona_web_so_por_dizer_atual():
    pergunta = "Analise os pedidos atuais do CRM e informe a próxima etapa de cada um."
    requeridas = _fontes_requeridas_ia003(pergunta)
    assert "pedidos" in requeridas
    assert "web" not in requeridas


def test_web_explicita_continua_obrigatoria_e_sem_cruzamento_interno_implicito():
    pergunta = "Pesquise na web informações sobre lançamentos de refrigeração de transporte."
    assert _fontes_requeridas_ia003(pergunta) == {"web"}


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
    assert controle["controle_sintese_factual"] == "ia003_web_preservada_agente_com_fontes"
    assert controle["controle_web_proveniencia"] == "fontes_url_execucao_atual"
    assert controle["web_fontes_sintese"] == 2
    assert controle["web_urls_sintese"] == ["https://example.com/a", "https://example.com/b"]
