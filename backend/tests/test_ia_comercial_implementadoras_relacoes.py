from services import ia_comercial_agente as agente
from services import ia_comercial_sintese_factual as sintese
from services import ia_comercial_territorio_anfir as territorio


PERGUNTA = (
    "Quais implementadoras aparecem com maior frequência no DDD 011, com quais clientes e linhas "
    "elas estão relacionadas, e onde há sinais de atuação de concorrentes?"
)


def test_resumo_cruza_implementadora_cliente_linha_e_fabricante_no_mesmo_recorte():
    registros = [
        {
            "implementadora": "FIBRA WEST",
            "cliente": "CLIENTE A",
            "linha": "DT",
            "fabricante_equipamento": "THERMOKING",
        },
        {
            "implementadora": "FIBRA WEST",
            "cliente": "CLIENTE A",
            "linha": "DT",
            "fabricante_equipamento": "THERMOKING",
        },
        {
            "implementadora": "FIBRA WEST",
            "cliente": "CLIENTE B",
            "linha": "DD",
            "fabricante_equipamento": "RODOFRIO",
        },
        {
            "implementadora": "IBIPORÃ",
            "cliente": "CLIENTE C",
            "linha": "TR",
            "fabricante_equipamento": "CARRRIER",
        },
    ]

    resumo = territorio._resumir(registros)
    relacoes = resumo["relacoes_implementadoras"]

    assert relacoes[0]["implementadora"] == "FIBRA WEST"
    assert relacoes[0]["registros"] == 3
    assert relacoes[0]["clientes_por_registros"] == [
        {"valor": "CLIENTE A", "registros": 2},
        {"valor": "CLIENTE B", "registros": 1},
    ]
    assert relacoes[0]["linhas_por_registros"] == [
        {"valor": "DT", "registros": 2},
        {"valor": "DD", "registros": 1},
    ]
    assert relacoes[0]["fabricantes_equipamento_por_registros"] == [
        {"valor": "THERMOKING", "registros": 2},
        {"valor": "RODOFRIO", "registros": 1},
    ]
    assert relacoes[1]["implementadora"] == "IBIPORÃ"
    assert relacoes[1]["fabricantes_equipamento_por_registros"] == [
        {"valor": "CARRRIER", "registros": 1}
    ]


def test_sintese_expoe_relacoes_de_implementadoras_quando_pergunta_pede_concorrencia():
    resumo = territorio._resumir(
        [
            {
                "implementadora": "HIGH FLEX",
                "cliente": "FOOD CENTER",
                "linha": "DD",
                "fabricante_equipamento": "THERMOFLEX",
                "ddd": "011",
            }
        ]
    )

    relevante = sintese._resumo_territorial_relevante({"resumo": resumo}, PERGUNTA)

    assert relevante["ranking_implementadoras"] == [{"valor": "HIGH FLEX", "registros": 1}]
    assert relevante["relacoes_implementadoras"][0]["clientes_por_registros"] == [
        {"valor": "FOOD CENTER", "registros": 1}
    ]
    assert relevante["relacoes_implementadoras"][0]["linhas_por_registros"] == [
        {"valor": "DD", "registros": 1}
    ]
    assert relevante["relacoes_implementadoras"][0]["fabricantes_equipamento_por_registros"] == [
        {"valor": "THERMOFLEX", "registros": 1}
    ]
    assert "coocorrência histórica" in relevante["regra_relacoes_implementadoras"]


def test_planejamento_territorial_implementadoras_nao_expande_clientes_produtos_ou_historico():
    assert agente._fontes_requeridas(PERGUNTA) == {"territorio"}

    historica = (
        "No histórico do DDD 011, quais implementadoras aparecem com quais clientes e linhas "
        "e quais sinais de concorrência existem?"
    )
    assert agente._fontes_requeridas(historica) == {"territorio"}


def test_planejamento_implementadoras_so_expande_quando_pedido_explicitamente():
    com_catalogo = PERGUNTA + " Compare também com o catálogo e os produtos disponíveis."
    assert agente._fontes_requeridas(com_catalogo) == {"territorio", "produtos"}

    com_pipeline = PERGUNTA + " Verifique também as oportunidades abertas no pipeline."
    assert agente._fontes_requeridas(com_pipeline) == {"territorio", "oportunidades"}


def test_instrucoes_proibem_transformar_coocorrencia_em_relacionamento_ativo():
    instrucoes = sintese.INSTRUCOES_SINTESE_FATUAL.casefold()
    assert "coocorrência factual" in instrucoes
    assert "não as transforme em contrato" in instrucoes
    assert "classificacao_fabricantes_equipamento.concorrentes" in instrucoes
    assert "nunca pode ser chamado de concorrente" in instrucoes
