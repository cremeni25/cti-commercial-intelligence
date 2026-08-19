import inspect

from routers.backoffice_fontes_promocao_router import detalhe_conflito_promocao, promover_reconciliacao


def test_detalhe_conflito_promocao_preserva_contexto_do_item():
    item = {
        "id": "item-1",
        "indice_semantico": 7,
        "entidade_sugerida": "CLIENTE",
        "natureza_canonica": "CRM_CADASTRAL",
    }
    detalhe = detalhe_conflito_promocao(item, ValueError("campo cidade divergente"))

    assert detalhe == {
        "tipo": "DIVERGENCIA_PROMOCAO",
        "item_id": "item-1",
        "indice_semantico": 7,
        "entidade": "CLIENTE",
        "natureza_canonica": "CRM_CADASTRAL",
        "mensagem": "campo cidade divergente",
        "regra": "CTI_PROMOCAO_CONFLITO_RASTREAVEL_V1",
    }


def test_router_transforma_valueerror_de_promocao_em_conflito_e_409():
    fonte = inspect.getsource(promover_reconciliacao)

    assert '"status_item": "CONFLITO"' in fonte
    assert '"status": "EM_REVISAO"' in fonte
    assert '"tipo": "CONFLITO_RECONCILIACAO"' in fonte
    assert '"PROMOCAO_BLOQUEADA_CONFLITO"' in fonte
    assert "raise HTTPException(status_code=409" in fonte
    assert "except HTTPException:" in fonte
