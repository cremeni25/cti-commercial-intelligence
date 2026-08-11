from __future__ import annotations

import pytest

from services import ia_comercial_sintese_crm as multifonte
from services.ia_comercial_cti import IAComercialOpenAIError


def test_cruzamento_expresso_web_portfolio_vendas_restringe_fontes():
    pergunta = (
        "Quais são as novidades recentes do mercado de transporte refrigerado e como elas se comparam "
        "com nosso portfólio e nossas vendas no CTI?"
    )
    requeridas = multifonte._fontes_requeridas_ia004(pergunta)
    assert requeridas == {"web", "produtos", "vendas"}

    ferramentas, nomes = multifonte._ferramentas_permitidas_multifonte(requeridas)
    assert nomes == {"web_search", "consultar_catalogo_produtos_cti", "consultar_dominio_cti"}
    assert all(
        (item.get("type") == "web_search")
        or item.get("name") in {"consultar_catalogo_produtos_cti", "consultar_dominio_cti"}
        for item in ferramentas
    )

    dominio = next(item for item in ferramentas if item.get("name") == "consultar_dominio_cti")
    assert dominio["parameters"]["properties"]["dominio"]["enum"] == ["vendas"]


def test_multifonte_nao_libera_anfir_territorio_clientes_sem_pedido():
    requeridas = {"web", "produtos", "vendas"}
    ferramentas, nomes = multifonte._ferramentas_permitidas_multifonte(requeridas)
    assert "consultar_anfir_cti" not in nomes
    assert "consultar_territorio_cti" not in nomes
    assert "consultar_historico_cti" not in nomes
    dominio = next(item for item in ferramentas if item.get("name") == "consultar_dominio_cti")
    assert "clientes" not in dominio["parameters"]["properties"]["dominio"]["enum"]


def test_auditoria_rejeita_dominio_cti_fora_do_escopo_multifonte():
    metadados = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_dominio_cti",
                "argumentos": {"dominio": "clientes"},
            }
        ]
    }
    with pytest.raises(IAComercialOpenAIError) as exc:
        multifonte._auditar_ferramentas_multifonte(metadados, {"web", "produtos", "vendas"})
    assert exc.value.codigo == "AGENT_MULTISOURCE_SCOPE_VIOLATION"


def test_portfolio_amplo_nao_usa_tema_generico_como_filtro_textual():
    argumentos = multifonte._normalizar_argumentos_multifonte(
        "consultar_catalogo_produtos_cti",
        {"termo": "transporte refrigerado"},
        {"web", "produtos", "vendas"},
        "Compare o mercado com nosso portfólio e nossas vendas no CTI.",
    )
    assert argumentos["termo"] is None


def test_vendas_amplas_nao_usam_tema_generico_como_filtro_textual():
    argumentos = multifonte._normalizar_argumentos_multifonte(
        "consultar_dominio_cti",
        {"dominio": "vendas", "termo": "transporte refrigerado", "status": None, "limite": 10, "offset": 0},
        {"web", "produtos", "vendas"},
        "Compare o mercado com nosso portfólio e nossas vendas no CTI.",
    )
    assert argumentos["termo"] is None
    assert argumentos["status"] is None
    assert argumentos["offset"] == 0
    assert argumentos["limite"] == 100


def test_ausencia_em_dominio_nao_consultado_e_removida_da_sintese():
    texto, ajustes = multifonte._sanitizar_ausencias_nao_consultadas(
        "DADOS INTERNOS CTI:\n- Não foram encontradas oportunidades comerciais ativas nem registros de clientes vinculados.\n- Existem três vendas registradas.",
        {"web", "produtos", "vendas"},
    )
    assert ajustes == 1
    assert "Não foram encontradas oportunidades" not in texto
    assert "Existem três vendas registradas" in texto
    assert "não consultados" in texto


def test_sintese_remove_termo_inventado_quando_vendas_foram_consultadas_sem_filtro():
    metadados = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_dominio_cti",
                "argumentos": {"dominio": "vendas", "termo": None, "status": None, "limite": 100, "offset": 0},
            }
        ]
    }
    texto, ajustes = multifonte._sanitizar_filtros_inexistentes(
        'Entre as vendas recentes registradas no CTI relacionadas ao termo "elétrica" há três ocorrências.',
        metadados,
    )
    assert ajustes == 1
    assert "relacionadas ao termo" not in texto
    assert "há três ocorrências" in texto


def test_sintese_preserva_termo_quando_filtro_foi_realmente_executado():
    metadados = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_dominio_cti",
                "argumentos": {"dominio": "vendas", "termo": "elétrica", "status": None, "limite": 100, "offset": 0},
            }
        ]
    }
    original = 'Vendas relacionadas ao termo "elétrica": três ocorrências.'
    texto, ajustes = multifonte._sanitizar_filtros_inexistentes(original, metadados)
    assert ajustes == 0
    assert texto == original


def test_sintese_multifonte_registra_proveniencia_segregada():
    metadados = {
        "evidencias_requeridas": ["web", "produtos", "vendas"],
        "evidencias_atendidas": ["web", "produtos", "vendas", "relacionamentos_vendas"],
        "fontes": [
            {"tipo": "WEB", "descricao": "Fonte A", "url": "https://example.com/a"},
            {"tipo": "WEB", "descricao": "Fonte B", "url": "https://example.com/b"},
        ],
    }
    texto, controle = multifonte.sintetizar_fatos_execucao(
        "Compare novidades do mercado com nosso portfólio e nossas vendas no CTI.",
        metadados,
        "usuario",
        "ADMIN_MASTER",
    )
    assert texto is None
    assert controle["controle_sintese_factual"] == "ia004_multifonte_preservada_com_proveniencia"
    assert controle["controle_multifonte_proveniencia"] == "externo_interno_inferencia_segregados"
    assert controle["multifonte_fontes_internas_sintese"] == ["produtos", "vendas"]
    assert controle["web_fontes_sintese"] == 2


def test_execucao_web_pura_continua_fora_da_restricao_multifonte():
    ferramentas, nomes = multifonte._ferramentas_permitidas_multifonte({"web"})
    assert nomes == set()
    assert any(item.get("type") == "web_search" for item in ferramentas)
