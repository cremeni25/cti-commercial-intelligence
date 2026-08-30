from services import commercial_client_scope as scope


def test_conta_direta_master_nao_reaparece_no_territorio(monkeypatch):
    monkeypatch.setattr(scope, "_mapa_clientes", lambda: {
        "CLIENTEA": {"nome": "Cliente A", "responsavel_comercial_id": "michele", "responsabilidade_tipo": "TERRITORIO"},
        "CLIENTEB": {"nome": "Cliente B", "responsavel_comercial_id": "master", "responsabilidade_tipo": "CONTA_DIRETA_MASTER"},
    })
    registros = [
        {"empresa": "Cliente A", "ddd": "011", "sub_regiao": "REGIAO 02"},
        {"empresa": "Cliente B", "ddd": "011", "sub_regiao": "REGIAO 02"},
        {"empresa": "Sem cadastro reconciliado", "ddd": "011", "sub_regiao": "REGIAO 02"},
    ]
    resultado = scope.filtrar_por_responsabilidade_cliente(registros, "michele")
    assert [item["empresa"] for item in resultado] == ["Cliente A", "Sem cadastro reconciliado"]
