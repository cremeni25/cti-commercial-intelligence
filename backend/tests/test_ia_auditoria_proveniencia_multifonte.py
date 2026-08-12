from services.ia_comercial_auditoria_evidencial import construir_auditoria_evidencial


def _metadados_multifonte():
    return {
        "fontes": [
            {
                "tipo": "WEB",
                "descricao": "Randon, Facchini, Librelato e Guerra no TOP 20 da indústria global",
                "url": "https://example.com/randon-facchini-librelato-guerra",
            },
            {
                "tipo": "WEB",
                "descricao": "Lista de grandes fabricantes de carrocerias no Brasil",
                "url": "https://example.com/grandes-carrocerias",
            },
        ],
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_universo_cti",
                "argumentos": {
                    "fonte": "historico_anfir",
                    "agrupar_por": ["implementadora"],
                    "metricas": [{"operacao": "count", "campo": None, "alias": "total_registros"}],
                },
                "resumo": {"erro": None},
            }
        ],
        "evidencias_requeridas": ["universo_cti", "web"],
        "evidencias_atendidas": ["universo_cti", "web"],
    }


def test_prosa_multifonte_preserva_proveniencia_por_bloco_narrativo():
    resposta = """No universo histórico autorizado pelo CTI, as cinco implementadoras com maior número de registros são:

1. IBIPORÃ — 1.118 registros
2. PAVAN — 763 registros

Esses números representam a quantidade de registros históricos no CTI, sem equivaler a market share.

Separadamente, pesquisa na web indica algumas das principais implementadoras do mercado brasileiro:

- Randon Implementos
- Facchini S.A.
- Librelato S.A.
- Guerra Implementos Rodoviários
- Comil Ônibus S.A.

Assim, o ranking interno CTI e o ranking externo apresentam diferenças de fonte e métrica.
"""

    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados_multifonte(),
        pergunta_atual="relacione as maiores usando CTI e web",
    )
    afirmacoes = resultado["auditoria_evidencial"]["afirmacoes"]

    por_texto = {item["texto"]: item for item in afirmacoes}

    assert por_texto["IBIPORÃ — 1.118 registros"]["tipo"] == "FATO_CTI"
    assert por_texto["IBIPORÃ — 1.118 registros"]["fontes_evidencia"] == ["CTI_1"]

    for entidade in (
        "Randon Implementos",
        "Facchini S.A.",
        "Librelato S.A.",
        "Guerra Implementos Rodoviários",
        "Comil Ônibus S.A.",
    ):
        assert por_texto[entidade]["tipo"] == "FATO_WEB"
        assert por_texto[entidade]["fontes_evidencia"]
        assert all(fonte.startswith("WEB_") for fonte in por_texto[entidade]["fontes_evidencia"])

    conclusao = por_texto["Assim, o ranking interno CTI e o ranking externo apresentam diferenças de fonte e métrica."]
    assert conclusao["tipo"] == "INFERENCIA_RECOMENDACAO"
    assert "CTI_1" in conclusao["derivada_de"]
    assert any(fonte.startswith("WEB_") for fonte in conclusao["derivada_de"])
    assert resultado["auditoria_afirmacoes_sem_evidencia"] == 0


def test_coincidencia_de_nome_nao_transforma_bloco_web_em_fato_cti():
    resposta = """No universo histórico autorizado pelo CTI, RANDON aparece no ranking interno.

Separadamente, pesquisa na web indica empresas reconhecidas no mercado:
- RANDON
- Facchini
"""
    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados_multifonte(),
        pergunta_atual="compare CTI e web",
    )
    afirmacoes = resultado["auditoria_evidencial"]["afirmacoes"]
    randons = [item for item in afirmacoes if item["texto"] == "RANDON"]

    assert len(randons) == 1
    assert randons[0]["tipo"] == "FATO_WEB"
    assert all(fonte.startswith("WEB_") for fonte in randons[0]["fontes_evidencia"])
