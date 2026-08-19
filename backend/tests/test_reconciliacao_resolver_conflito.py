import inspect

import pytest

from routers.backoffice_fontes_reconciliacao_router import (
    avaliar_resolucao_conflito,
    resolver_conflito_reconciliacao,
)


def test_resolucao_revalida_natureza_canonica_antes_de_liberar():
    item = {"indice_semantico": 12, "status_item": "CONFLITO"}

    reavaliado = avaliar_resolucao_conflito(
        "COMERCIAL",
        item,
        {"nome": "Cliente Corrigido", "cnpj": "12.345.678/0001-90"},
    )

    assert reavaliado["status_item"] == "VALIDO"
    assert reavaliado["entidade_sugerida"] == "CLIENTE"
    assert reavaliado["natureza_canonica"] == "CRM_CADASTRAL"
    assert reavaliado["camada_dashboard"] == "CADASTRO_CRM"
    assert reavaliado["conflitos"] == []


def test_resolucao_nao_libera_dados_ainda_sem_natureza_comercial():
    item = {"indice_semantico": 13, "status_item": "CONFLITO"}

    with pytest.raises(ValueError, match="ainda possuem conflito semântico"):
        avaliar_resolucao_conflito("COMERCIAL", item, {"observacao": "sem identificador"})


def test_resolucao_exige_dados_corrigidos_estruturados():
    with pytest.raises(ValueError, match="dados corrigidos estruturados"):
        avaliar_resolucao_conflito("COMERCIAL", {"indice_semantico": 1}, {})


def test_endpoint_reabre_aprovacao_e_audita_resolucao():
    fonte = inspect.getsource(resolver_conflito_reconciliacao)

    assert '"status_item": "VALIDO"' in fonte
    assert '"conflitos": []' in fonte
    assert '"aprovado_por": None' in fonte
    assert '"aprovado_em": None' in fonte
    assert '"RECONCILIACAO_CONFLITO_RESOLVIDO"' in fonte
    assert '"requer_nova_aprovacao": True' in fonte
