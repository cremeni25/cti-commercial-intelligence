import inspect

from core.ingestion_promotion import DivergenciaPromocao
from routers.backoffice_fontes_promocao_router import (
    detalhe_conflito_promocao,
    detalhes_conflito_promocao,
    promover_reconciliacao,
)


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
        "regra": "CTI_PROMOCAO_CONFLITO_RASTREAVEL_V2_ESTRUTURADO",
    }


def test_detalhes_conflito_promocao_expande_divergencias_por_campo():
    item = {
        "id": "item-2",
        "indice_semantico": 8,
        "entidade_sugerida": "CLIENTE",
        "natureza_canonica": "CRM_CADASTRAL",
    }
    erro = DivergenciaPromocao(
        "Cliente existente possui divergências; promoção não sobrescreveu dados.",
        [
            {"campo": "cidade", "valor_existente": "Campinas", "valor_recebido": "Santos"},
            {"campo": "estado", "valor_existente": "SP", "valor_recebido": "RJ"},
        ],
    )

    detalhes = detalhes_conflito_promocao(item, erro)

    assert len(detalhes) == 2
    assert detalhes[0]["campo"] == "cidade"
    assert detalhes[0]["valor_existente"] == "Campinas"
    assert detalhes[0]["valor_recebido"] == "Santos"
    assert detalhes[1]["campo"] == "estado"
    assert all(d["item_id"] == "item-2" for d in detalhes)
    assert all(d["regra"] == "CTI_PROMOCAO_CONFLITO_RASTREAVEL_V2_ESTRUTURADO" for d in detalhes)


def test_router_transforma_valueerror_de_promocao_em_conflito_e_409():
    fonte = inspect.getsource(promover_reconciliacao)

    assert '"status_item": "CONFLITO"' in fonte
    assert '"conflitos": conflitos' in fonte
    assert '"status": "EM_REVISAO"' in fonte
    assert '"tipo": "CONFLITO_RECONCILIACAO"' in fonte
    assert '"PROMOCAO_BLOQUEADA_CONFLITO"' in fonte
    assert "raise HTTPException(status_code=409" in fonte
    assert "except HTTPException:" in fonte
