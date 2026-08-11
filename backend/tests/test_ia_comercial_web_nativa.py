from __future__ import annotations

from services.ia_comercial_agente_crm import (
    _fontes_requeridas_ia003,
    _necessita_web_autonoma,
)
from services.ia_comercial_sintese_crm import sintetizar_fatos_execucao


def test_web_e_exigida_sem_comando_explicito_quando_fato_externo_e_atual():
    pergunta = (
        "Quais são as novidades mais recentes da Thermo King para refrigeração de transporte "
        "no Brasil e o que isso pode significar comercialmente para a operação Carrier/Viena?"
    )
    assert _necessita_web_autonoma(pergunta) is True
    assert "web" in _fontes_requeridas_ia003(pergunta)


def test_pergunta_atual_do_crm_nao_aciona_web_so_por_dizer_atual():
    pergunta = "Analise os pedidos atuais do CRM e informe a próxima etapa de cada um."
    requeridas = _fontes_requeridas_ia003(pergunta)
    assert "pedidos" in requeridas
    assert "web" not in requeridas


def test_web_explicita_continua_obrigatoria():
    assert "web" in _fontes_requeridas_ia003(
        "Pesquise na web informações sobre lançamentos de refrigeração de transporte."
    )


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
