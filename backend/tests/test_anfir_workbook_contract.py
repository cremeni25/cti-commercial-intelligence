from services.anfir_workbook_contract import consolidar_workbook_anfir_2026


def _r(cliente, linha, status, motivo="", ocorrencia="", implementadora="IBIPORA", mes=1, ddd="011"):
    return {
        "cliente": cliente,
        "linha": linha,
        "status": status,
        "motivo": motivo,
        "ocorrencia": ocorrencia,
        "implementadora": implementadora,
        "ano_referencia": 2026,
        "mes": mes,
        "ddd": ddd,
    }


def test_contrato_reproduz_as_quatro_abas_logicas_do_workbook():
    registros = [
        _r("CLIENTE A", "Trailer", "Carrier", mes=1),
        _r("CLIENTE A", "Trailer", "TK", ocorrencia="Cliente utiliza Thermo King", mes=4),
        _r("CLIENTE B", "Diesel Truck", "Sem contato", motivo="Não participamos da proposta", ocorrencia="Falta contato e relacionamento", mes=2, ddd="014"),
        _r("CLIENTE C", "Direct Drive", "Nacional", motivo="Não participamos da proposta", ocorrencia="Implementadora fabrica o equipamento e oferece Frigoking incluso no valor", mes=5, ddd="015"),
        _r("CLIENTE C", "Direct Drive", "Nacional", motivo="Preço Carrier mais alto", ocorrencia="Preço e solução técnica influenciaram", mes=6, ddd="015"),
    ]

    payload = consolidar_workbook_anfir_2026(registros)

    assert payload["metadata"]["nome_contrato"] == "Auditoria_ANFIR_Carrier_JOV_2026_Inteligencia_Viena_Observacoes"
    assert set(payload) == {
        "metadata",
        "inteligencia_viena",
        "oportunidades_prioritarias",
        "implementadoras_mercado",
        "inteligencia_observacoes",
    }
    assert payload["inteligencia_viena"]["mercado_elegivel"] == 5
    assert payload["inteligencia_viena"]["carrier_observada"] == 1
    assert {item["codigo"]: item["mercado"] for item in payload["inteligencia_viena"]["segmentos"]} == {"TR": 2, "DT": 1, "DD": 2}


def test_priorizacao_mantem_score_transparente_da_planilha():
    registros = [
        _r("CLIENTE X", "Direct Drive", "Nacional", motivo="Não participamos da proposta", ocorrencia="Preço alto"),
        _r("CLIENTE X", "Direct Drive", "Sem contato", ocorrencia="Sem contato"),
    ]
    payload = consolidar_workbook_anfir_2026(registros)
    item = payload["oportunidades_prioritarias"][0]

    # não Carrier=2 + 2*(não participou=1 + sem contato=1); preço não soma aqui
    # porque a causa estruturada da primeira ocorrência é COBERTURA_COMERCIAL.
    assert item["score_transparente"] == 6
    assert item["criterio_score"] == "não Carrier + 2×(não participou + sem contato) + preço + relacionamento + gap técnico"


def test_observacao_original_alimenta_multiplos_temas_sem_exclusividade():
    registros = [
        _r(
            "CLIENTE Y",
            "Direct Drive",
            "Nacional",
            ocorrencia="Implementadora fabrica o equipamento Frigoking incluso no valor; preço e solução técnica em discussão",
        )
    ]
    payload = consolidar_workbook_anfir_2026(registros)
    temas = {item["tema"] for item in payload["inteligencia_observacoes"]["temas"]}

    assert "IMPLEMENTADORA_INTEGRADA" in temas
    assert "CONCORRENTE_NACIONAL" in temas
    assert "PRECO_VALOR" in temas
    assert "TECNICO_PRODUTO" in temas
    assert payload["inteligencia_observacoes"]["regra"] == "Texto original preservado; temas derivados são auxiliares e podem coexistir."
