from core.ingestion_reconciliation import avaliar_item, preparar_plano


def _item(indice: int, dados: dict):
    return {"indice": indice, "dados": dados}


def test_anfir_permanece_mercado_realizado_e_nao_funil():
    item = avaliar_item("MERCADO_ANFIR", _item(1, {"chassi": "ABC123", "implementadora": "RANDON"}))
    assert item["entidade_sugerida"] == "ANFIR"
    assert item["natureza_canonica"] == "MERCADO_REALIZADO"
    assert item["camada_dashboard"] == "REALIZADO_MERCADO"


def test_oportunidade_comercial_permanece_funil_em_curso():
    item = avaliar_item("COMERCIAL", _item(2, {"numero_oportunidade": "OP-001", "cliente": "Cliente A"}))
    assert item["entidade_sugerida"] == "OPORTUNIDADE"
    assert item["natureza_canonica"] == "FUNIL_COMERCIAL"
    assert item["camada_dashboard"] == "EM_CURSO_FUNIL"


def test_cliente_crm_nao_vira_funil_sem_oportunidade():
    item = avaliar_item("COMERCIAL", _item(3, {"cnpj": "123", "nome": "Cliente A"}))
    assert item["entidade_sugerida"] == "CLIENTE"
    assert item["natureza_canonica"] == "CRM_CADASTRAL"
    assert item["camada_dashboard"] == "CADASTRO_CRM"


def test_venda_e_realizado_comercial_sem_confundir_com_anfir():
    item = avaliar_item("COMERCIAL", _item(4, {"numero_venda": "VEN-001", "cliente": "Cliente A"}))
    assert item["entidade_sugerida"] == "VENDA"
    assert item["natureza_canonica"] == "COMERCIAL_REALIZADO"
    assert item["camada_dashboard"] == "REALIZADO_COMERCIAL"


def test_plano_misto_preserva_camadas_sem_fundir_registros():
    plano = preparar_plano("COMERCIAL", [
        _item(1, {"cnpj": "1", "nome": "Cliente A"}),
        _item(2, {"numero_oportunidade": "OP-1", "cliente": "Cliente A"}),
        _item(3, {"numero_venda": "VEN-1", "cliente": "Cliente A"}),
    ])
    assert plano["naturezas"] == {
        "CRM_CADASTRAL": 1,
        "FUNIL_COMERCIAL": 1,
        "COMERCIAL_REALIZADO": 1,
    }
    assert plano["camadas_dashboard"] == {
        "CADASTRO_CRM": 1,
        "EM_CURSO_FUNIL": 1,
        "REALIZADO_COMERCIAL": 1,
    }
    assert plano["lote_misto_naturezas"] is True
    assert plano["roteamento_por_registro"] is True
    assert plano["regra"] == "CTI_RECONCILIACAO_CONTROLADA_V3_NATUREZA_POR_REGISTRO"
