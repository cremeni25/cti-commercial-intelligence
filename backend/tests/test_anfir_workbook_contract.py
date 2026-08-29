from services.anfir_workbook_contract import consolidar_workbook_anfir_2026


def _r(cliente, linha, status, motivo="", ocorrencia="", implementadora="IBIPORA", mes=1, ddd="011", cidade="SAO PAULO"):
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
        "estado": "SP",
        "cidade": cidade,
    }


def test_contrato_reproduz_as_quatro_abas_logicas_do_workbook():
    registros = [
        _r("CLIENTE A", "Trailer", "Carrier", mes=1),
        _r("CLIENTE A", "Trailer", "TK", ocorrencia="Cliente utiliza Thermo King", mes=4),
        _r("CLIENTE B", "Diesel Truck", "Sem contato", motivo="Não participamos da proposta", mes=2, ddd="014", cidade="JAU"),
        _r("CLIENTE C", "Direct Drive", "Nacional", motivo="Não participamos da proposta", mes=5, ddd="015", cidade="SOROCABA"),
        _r("CLIENTE C", "Direct Drive", "Nacional", motivo="Preço Carrier mais alto", mes=6, ddd="015", cidade="SOROCABA"),
    ]
    payload = consolidar_workbook_anfir_2026(registros)
    assert payload["metadata"]["nome_contrato"] == "Auditoria_ANFIR_Carrier_JOV_2026_Inteligencia_Viena_Observacoes"
    assert set(payload) == {"metadata", "inteligencia_viena", "oportunidades_prioritarias", "implementadoras_mercado", "inteligencia_observacoes"}
    assert payload["inteligencia_viena"]["mercado_elegivel"] == 5
    assert payload["inteligencia_viena"]["carrier_observada"] == 1
    assert {item["codigo"]: item["mercado"] for item in payload["inteligencia_viena"]["segmentos"]} == {"TR": 2, "DT": 1, "DD": 2}


def test_priorizacao_mantem_score_transparente_da_planilha():
    registros = [
        _r("CLIENTE X", "Direct Drive", "Nacional", motivo="Não participamos da proposta"),
        _r("CLIENTE X", "Direct Drive", "Sem contato"),
    ]
    payload = consolidar_workbook_anfir_2026(registros)
    item = payload["oportunidades_prioritarias"][0]
    assert item["score_transparente"] == 6
    assert item["criterio_score"] == "não Carrier + 2×(não participou + sem contato) + preço + relacionamento + gap técnico"


def test_causa_workbook_prioriza_motivo_original_e_nao_texto_do_plano():
    registros = [
        _r("MIXTER", "Diesel Truck", "Nacional", motivo="Utilizou o seu próprio equipamento usado", ocorrencia="REPRESENTAÇÃO: JOV\nOBSERVAÇÃO: Thermostar - Cliente NAGUMO Supermercados, comprou 15 implementos. CARLA esta em cima para iniciar relacionamento\nPLANO AÇÃO 1: Cliente visitado, está entrando em contato com o responsável."),
        _r("MIXTER", "Diesel Truck", "Nacional", motivo="Falta de relacionamento"),
    ]
    item = consolidar_workbook_anfir_2026(registros)["oportunidades_prioritarias"][0]
    assert item["relacionamento"] == 1
    assert item["preco"] == 0


def test_observacao_original_reproduz_multitemas_do_workbook():
    observacao = "Equipamentos elétricos e caminhões elétricos - operação Pacheco São Paulo, participamos, mas não avançamos com o teste do NEOS (Por preço)."
    registro = _r("EVM", "Direct Drive", "Nacional", motivo="Sem solução técnica apropriada", ocorrencia=f"REPRESENTAÇÃO: JOV\nOBSERVAÇÃO: {observacao}\nPLANO AÇÃO 1: Verificar com comercial (Projeto elétrico Addvolt)\nQUANDO: Imediato")
    payload = consolidar_workbook_anfir_2026([registro])
    temas = {item["tema"] for item in payload["inteligencia_observacoes"]["temas"]}
    assert temas == {"TECNICA_PRODUTO", "PRECO_VALOR", "PARTICIPACAO_TESTE", "CONTEXTO_CLIENTE"}
    assert payload["inteligencia_observacoes"]["com_observacao_util"] == 1


def test_ddd_municipal_da_auditoria_prevalece_sobre_ddd_legado_conflitante():
    registro = _r("CLIENTE SP", "Direct Drive", "Nacional", ddd="015", cidade="SAO PAULO")
    territorio = consolidar_workbook_anfir_2026([registro])["inteligencia_viena"]["territorio"]
    por_ddd = {item["ddd"]: item["mercado"] for item in territorio}
    assert por_ddd["011"] == 1
    assert por_ddd["015"] == 0


def test_placeholder_de_status_permanece_dado_a_qualificar():
    payload = consolidar_workbook_anfir_2026([_r("CLIENTE", "Direct Drive", "#N/A")])
    assert payload["inteligencia_viena"]["dados_status_a_qualificar"] == 1
    dd = next(item for item in payload["inteligencia_viena"]["segmentos"] if item["codigo"] == "DD")
    assert dd["nao_classificado"] == 1
