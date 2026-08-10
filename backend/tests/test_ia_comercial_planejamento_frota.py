from services.ia_comercial_agente import _fontes_requeridas


def test_frota_territorial_nao_expande_historico_ou_catalogo():
    pergunta = (
        "Analise a frota registrada no DDD 011. Diferencie registros históricos de veículos identificáveis, "
        "mostre a cobertura de placa e chassi e indique os principais fabricantes e modelos de caminhão encontrados. "
        "Não trate registros repetidos como veículos diferentes."
    )

    assert _fontes_requeridas(pergunta) == {"territorio"}


def test_frota_territorial_so_adiciona_catalogo_quando_explicito():
    pergunta = "No DDD 011, analise a frota e compare os modelos de caminhão com os modelos disponíveis no catálogo."

    assert _fontes_requeridas(pergunta) == {"territorio", "produtos"}


def test_frota_territorial_pode_exigir_anfir_quando_explicitamente_pedido():
    pergunta = "Analise a frota do DDD 011 e compare com os dados ANFIR disponíveis."

    assert _fontes_requeridas(pergunta) == {"territorio", "anfir"}
