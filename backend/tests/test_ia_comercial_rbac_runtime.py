from services import ia_comercial_rbac_runtime as modulo


def base_dados():
    return {
        "clientes": [
            {"id": "cli-1", "nome": "Cliente Compartilhado"},
            {"id": "cli-2", "nome": "Outro Cliente"},
        ],
        "oportunidades": [
            {"id": "opp-1", "cliente_id": "cli-1", "responsavel_id": "user-1"},
            {"id": "opp-2", "cliente_id": "cli-1", "responsavel_id": "user-2"},
        ],
        "itens": [
            {"id": "item-1", "oportunidade_id": "opp-1"},
            {"id": "item-2", "oportunidade_id": "opp-2"},
        ],
        "propostas": [
            {"id": "prop-1", "cliente_id": "cli-1", "item_oportunidade_id": "item-1"},
            {"id": "prop-2", "cliente_id": "cli-1", "item_oportunidade_id": "item-2"},
        ],
        "aceites": [
            {"id": "aceite-1", "proposta_id": "prop-1"},
            {"id": "aceite-2", "proposta_id": "prop-2"},
        ],
        "pedidos": [
            {"id": "ped-1", "cliente_id": "cli-1", "proposta_id": "prop-1"},
            {"id": "ped-2", "cliente_id": "cli-1", "proposta_id": "prop-2"},
        ],
        "atividades": [
            {"id": "atv-1", "cliente_id": "cli-1", "usuario_id": "user-1"},
            {"id": "atv-2", "cliente_id": "cli-1", "usuario_id": "user-2"},
        ],
        "vendas": [
            {"id": "venda-1", "cliente_id": "cli-1", "pedido_id": "ped-1"},
            {"id": "venda-2", "cliente_id": "cli-1", "pedido_id": "ped-2"},
        ],
    }


def instalar(monkeypatch):
    dados = base_dados()
    monkeypatch.setattr(modulo.dados, "_carregar_dominio", lambda dominio: list(dados[dominio]))
    return dados


def ids(colecao):
    return {item["id"] for item in colecao}


def test_diretor_viena_recebe_visao_consolidada(monkeypatch):
    dados = instalar(monkeypatch)
    retorno = modulo.escopo_crm_autorizado("diretor-1", "DIRETOR_VIENA_SP")
    assert ids(retorno["oportunidades"]) == ids(dados["oportunidades"])
    assert ids(retorno["pedidos"]) == ids(dados["pedidos"])
    assert ids(retorno["atividades"]) == ids(dados["atividades"])


def test_regional_nao_herda_negocio_alheio_por_cliente_compartilhado(monkeypatch):
    instalar(monkeypatch)
    retorno = modulo.escopo_crm_autorizado("user-1", "REPRES_REGIAO_01")
    assert ids(retorno["oportunidades"]) == {"opp-1"}
    assert ids(retorno["itens"]) == {"item-1"}
    assert ids(retorno["propostas"]) == {"prop-1"}
    assert ids(retorno["aceites"]) == {"aceite-1"}
    assert ids(retorno["pedidos"]) == {"ped-1"}
    assert ids(retorno["atividades"]) == {"atv-1"}
    assert ids(retorno["vendas"]) == {"venda-1"}
    assert ids(retorno["clientes"]) == {"cli-1"}


def test_patch_substitui_funcao_usada_por_leitura_e_acoes():
    modulo.aplicar_patch_rbac_ia()
    assert modulo.universo._escopo_autorizado is modulo.escopo_crm_autorizado
    assert modulo.acoes._escopo_autorizado is modulo.escopo_crm_autorizado
