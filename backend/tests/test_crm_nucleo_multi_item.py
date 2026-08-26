from routers import crm_core_extension as core


def test_nucleo_comercial_soma_itens_ativos_antes_de_proposta_individual(monkeypatch):
    oportunidade_id = "opp-multi"
    tabelas = {
        "cti_oportunidades": [
            {
                "id": oportunidade_id,
                "cliente_id": "cli-1",
                "titulo": "Tomada de Preços",
                "status": "PROPOSTA",
                "valor_estimado": 1532304.60,
                "probabilidade": 50,
                "created_at": "2026-08-26T17:18:25+00:00",
            }
        ],
        "cti_oportunidade_itens": [
            {"id": "i1", "oportunidade_id": oportunidade_id, "equipamento": "SUPRA 750", "quantidade": 2, "preco_unitario": 105000, "desconto_percentual": 10.47, "status": "PROPOSTA_EMITIDA", "arquivado_em": None},
            {"id": "i2", "oportunidade_id": oportunidade_id, "equipamento": "SUPRA 1150", "quantidade": 6, "preco_unitario": 128000, "desconto_percentual": 4.68, "status": "PROPOSTA_EMITIDA", "arquivado_em": None},
            {"id": "i3", "oportunidade_id": oportunidade_id, "equipamento": "SUPRA 850", "quantidade": 6, "preco_unitario": 113000, "desconto_percentual": 9.70, "status": "PROPOSTA_EMITIDA", "arquivado_em": None},
        ],
        "cti_atividades": [],
        "cti_propostas": [
            {"id": "p1", "oportunidade_id": oportunidade_id, "item_oportunidade_id": "i1", "numero": "P1", "valor": 188013.00, "status_documento": "RASCUNHO", "versao": 1},
            {"id": "p2", "oportunidade_id": oportunidade_id, "item_oportunidade_id": "i2", "numero": "P2", "valor": 732057.60, "status_documento": "RASCUNHO", "versao": 1},
            {"id": "p3", "oportunidade_id": oportunidade_id, "item_oportunidade_id": "i3", "numero": "P3", "valor": 612234.00, "status_documento": "RASCUNHO", "versao": 1},
        ],
        "cti_pedidos": [],
        "cti_clientes": [],
        "clientes": [{"id": "cli-1", "nome": "PRIME CARGO LOGISTICA INTEGRADA LTDA"}],
    }

    monkeypatch.setattr(core, "_ler_tabela", lambda nome, obrigatoria=False: tabelas.get(nome, []))

    resultado = core.nucleo_comercial()

    assert len(resultado) == 1
    assert resultado[0]["etapa"] == "PROPOSTA"
    assert resultado[0]["quantidade_itens"] == 3
    assert resultado[0]["valor"] == 1532304.60
    assert resultado[0]["valor_ponderado"] == 766152.30


def test_nucleo_comercial_ignora_item_arquivado_no_total(monkeypatch):
    oportunidade_id = "opp-archive"
    tabelas = {
        "cti_oportunidades": [{"id": oportunidade_id, "cliente_id": "cli-1", "titulo": "Tomada de Preços", "status": "PROPOSTA", "probabilidade": 50, "created_at": "2026-08-26T17:18:25+00:00"}],
        "cti_oportunidade_itens": [
            {"id": "i1", "oportunidade_id": oportunidade_id, "quantidade": 1, "preco_unitario": 100000, "desconto_percentual": 0, "status": "PROPOSTA_EMITIDA", "arquivado_em": None},
            {"id": "i2", "oportunidade_id": oportunidade_id, "quantidade": 1, "preco_unitario": 900000, "desconto_percentual": 0, "status": "PROPOSTA_EMITIDA", "arquivado_em": "2026-08-26T18:00:00+00:00"},
        ],
        "cti_atividades": [], "cti_propostas": [], "cti_pedidos": [], "cti_clientes": [],
        "clientes": [{"id": "cli-1", "nome": "CLIENTE TESTE"}],
    }
    monkeypatch.setattr(core, "_ler_tabela", lambda nome, obrigatoria=False: tabelas.get(nome, []))

    resultado = core.nucleo_comercial()

    assert resultado[0]["quantidade_itens"] == 1
    assert resultado[0]["valor"] == 100000.00
