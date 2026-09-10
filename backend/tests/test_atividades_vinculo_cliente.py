from routers import crm_scope_router as scope


def test_atividade_sem_cliente_herda_cliente_da_oportunidade(monkeypatch):
    monkeypatch.setattr(
        scope,
        "obter_oportunidade",
        lambda oportunidade_id: {"id": oportunidade_id, "cliente_id": "cliente-123"},
    )

    atividade = {"id": "atividade-1", "oportunidade_id": "opp-1", "cliente_id": None}
    resultado = scope._vincular_clientes_atividades([atividade])[0]

    assert resultado["cliente_id"] == "cliente-123"
    assert resultado["vinculo_cliente_origem"] == "OPORTUNIDADE"


def test_atividade_preserva_cliente_explicito_sem_reinferir(monkeypatch):
    def falha(_):
        raise AssertionError("não deve consultar negociação quando cliente_id já existe")

    monkeypatch.setattr(scope, "obter_oportunidade", falha)
    atividade = {"id": "atividade-2", "cliente_id": "cliente-explicito", "oportunidade_id": "opp-2"}

    resultado = scope._vincular_clientes_atividades([atividade])[0]

    assert resultado["cliente_id"] == "cliente-explicito"
    assert "vinculo_cliente_origem" not in resultado


def test_atividade_pode_herdar_cliente_da_proposta_e_do_pedido(monkeypatch):
    monkeypatch.setattr(scope, "obter_oportunidade", lambda oportunidade_id: {"id": oportunidade_id, "cliente_id": "cliente-opp"})
    monkeypatch.setattr(
        scope,
        "obter_proposta",
        lambda proposta_id: {"id": proposta_id, "cliente_id": "cliente-proposta", "oportunidade_id": "opp-3"},
    )
    monkeypatch.setattr(
        scope,
        "obter_pedido",
        lambda pedido_id: {"id": pedido_id, "proposta_id": "prop-3"},
    )

    por_proposta = scope._vincular_clientes_atividades([{"id": "a3", "proposta_id": "prop-3"}])[0]
    por_pedido = scope._vincular_clientes_atividades([{"id": "a4", "pedido_id": "ped-3"}])[0]

    assert por_proposta["cliente_id"] == "cliente-proposta"
    assert por_proposta["vinculo_cliente_origem"] == "PROPOSTA"
    assert por_pedido["cliente_id"] == "cliente-proposta"
    assert por_pedido["vinculo_cliente_origem"] == "PEDIDO"
