from services.ia_comercial_artefatos import (
    construir_artefatos,
    detectar_intencao_artefato,
    extrair_serie_numerica,
    gerar_pdf_relatorio,
    gerar_svg_grafico,
)
from services.ia_comercial_artefatos_patch import _pedido_transformacao_artefato
from services.ia_comercial_artefatos_pos_sintese import _graficos_multifonte


RESPOSTA_IMPLEMENTADORAS = """Pela análise do histórico ANFIR disponível no CTI, as cinco implementadoras mais frequentes são:

1. Ibiporã — 1.118 registros
2. Pavan — 763 registros
3. Fibra West — 514 registros
4. High Flex — 305 registros
5. Randon — 240 registros

Esse ranking mede frequência histórica de registros.
"""

RESPOSTA_MULTIFONTE = """Internamente, pelo universo histórico ANFIR disponível no CTI, as cinco implementadoras com maior número de registros são:

1. Ibiporã — 1.118 registros
2. Pavan — 763 registros
3. Fibra West — 514 registros
4. High Flex — 305 registros
5. Randon — 240 registros

Complementando com dados da web, as cinco maiores por unidades emplacadas são:

1. Randon — 22.226 unidades (25,07% do mercado)
2. Facchini — 21.173 unidades (23,88%)
3. Librelato — 10.874 unidades (12,26%)
4. Guerra — 7.409 unidades (8,36%)
5. Truckvan — 2.123 unidades (2,39%)
"""


def test_pedido_real_reconhece_grafico():
    pedido = "De acordo com a resposta acima, gere um grafico utilizando a disposição das respostas apresentadas"
    assert detectar_intencao_artefato(pedido) == {"GRAFICO"}
    assert _pedido_transformacao_artefato(pedido, {"GRAFICO"}) is True


def test_relatorio_implica_pdf_baixavel():
    assert detectar_intencao_artefato("gere um relatório executivo desta análise") == {"RELATORIO", "PDF"}


def test_extracao_numerica_preserva_valores_reais():
    serie = extrair_serie_numerica(RESPOSTA_IMPLEMENTADORAS)
    assert [item["label"] for item in serie] == ["Ibiporã", "Pavan", "Fibra West", "High Flex", "Randon"]
    assert [item["valor"] for item in serie] == [1118.0, 763.0, 514.0, 305.0, 240.0]
    assert all(item["unidade"] == "registros" for item in serie)


def test_grafico_de_continuidade_usa_resposta_anterior_e_barra_por_padrao():
    artefatos = construir_artefatos(
        mensagem="De acordo com a resposta acima, gere um gráfico utilizando a disposição das respostas apresentadas",
        resposta_texto="Segue a mesma análise em formato solicitado.",
        historico=[{"role": "assistant", "content": RESPOSTA_IMPLEMENTADORAS}],
        fontes=[],
    )
    grafico = next(item for item in artefatos if item["tipo"] == "GRAFICO")
    assert grafico["fonte_dados"] == "resposta_anterior"
    assert grafico["formato"] == "BAR"
    assert len(grafico["dados"]) == 5
    assert grafico["dados"][0]["valor"] == 1118.0


def test_snapshot_final_multifonte_gera_dois_graficos_com_as_metricas_da_mesma_resposta():
    graficos = _graficos_multifonte(RESPOSTA_MULTIFONTE)
    assert len(graficos) == 2
    interno, externo = graficos
    assert interno["proveniencia"] == "CTI"
    assert interno["formato"] == "BAR"
    assert [item["valor"] for item in interno["dados"]] == [1118.0, 763.0, 514.0, 305.0, 240.0]
    assert externo["proveniencia"] == "WEB"
    assert externo["formato"] == "BAR"
    assert [item["label"] for item in externo["dados"]] == ["Randon", "Facchini", "Librelato", "Guerra", "Truckvan"]
    assert [item["valor"] for item in externo["dados"]] == [22226.0, 21173.0, 10874.0, 7409.0, 2123.0]
    assert all(item["unidade"] == "unidades" for item in externo["dados"])
    assert externo["dados"][0]["detalhe"] == "25,07% do mercado"


def test_formatos_linha_e_pizza_sao_deterministicos():
    linha = construir_artefatos(
        mensagem="gere um gráfico de linha desta evolução",
        resposta_texto=RESPOSTA_IMPLEMENTADORAS,
        historico=[],
        fontes=[],
    )
    pizza = construir_artefatos(
        mensagem="gere um gráfico de pizza desta composição",
        resposta_texto=RESPOSTA_IMPLEMENTADORAS,
        historico=[],
        fontes=[],
    )
    assert linha[0]["formato"] == "LINE"
    assert pizza[0]["formato"] == "PIE"
    assert b"<polyline" in gerar_svg_grafico({"artefatos": linha})
    assert b"<path" in gerar_svg_grafico({"artefatos": pizza})


def test_sem_serie_numerica_nao_inventa_grafico():
    artefatos = construir_artefatos(
        mensagem="gere um gráfico",
        resposta_texto="Não há números nesta análise.",
        historico=[],
        fontes=[],
    )
    grafico = artefatos[0]
    assert grafico["tipo"] == "GRAFICO"
    assert grafico["status"] == "SEM_SERIE_NUMERICA"
    assert "dados" not in grafico


def test_svg_e_pdf_sao_arquivos_validos():
    artefatos = construir_artefatos(
        mensagem="gere um relatório com gráfico e PDF para baixar",
        resposta_texto=RESPOSTA_IMPLEMENTADORAS,
        historico=[],
        fontes=[{"tipo": "CTI", "descricao": "Histórico ANFIR"}],
    )
    metadados = {"artefatos": artefatos, "fontes": [{"tipo": "CTI", "descricao": "Histórico ANFIR"}]}
    svg = gerar_svg_grafico(metadados)
    pdf = gerar_pdf_relatorio(RESPOSTA_IMPLEMENTADORAS, metadados, "Usuário CTI")
    assert svg.startswith(b"<svg")
    assert b"Ibipor" in svg
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
