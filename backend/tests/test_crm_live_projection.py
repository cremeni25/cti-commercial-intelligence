from services import crm_live_projection as projection
from routers.strategic_layers_router import _camada_crm
from routers.drilldown_router import _corresponde


def test_oportunidade_usa_todos_os_itens_ativos(monkeypatch):
    oportunidades = [{
        "id": "opp-1",
        "cliente_id": "cli-1",
        "titulo": "Tomada de Preços",
        "status": "PROPOSTA",
        "valor_estimado": 1532304.60,
        "descricao": "[CONTEXTO CTI]\nequipamentos: SUPRA 750\nmunicipio: BARUERI\nuf: SP\nddd: 11",
    }]
    itens = [
        {"oportunidade_id": "opp-1", "nome_comercial": "SUPRA 750", "linha_produto": "DIESEL TRUCK", "quantidade": 2, "arquivado_em": None},
        {"oportunidade_id": "opp-1", "nome_comercial": "SUPRA 1150", "linha_produto": "DIESEL TRUCK", "quantidade": 6, "arquivado_em": None},
        {"oportunidade_id": "opp-1", "nome_comercial": "SUPRA 850", "linha_produto": "DIESEL TRUCK", "quantidade": 6, "arquivado_em": None},
        {"oportunidade_id": "opp-1", "nome_comercial": "TESTE", "linha_produto": "DIESEL TRUCK", "quantidade": 1, "arquivado_em": "2026-08-26"},
    ]
    clientes = [{"id": "cli-1", "razao_social": "PRIME CARGO LOGISTICA INTEGRADA LTDA"}]

    def fake_lista(tabela):
        return {"cti_oportunidades": oportunidades, "cti_oportunidade_itens": itens, "clientes": clientes, "cti_clientes": []}.get(tabela, [])

    monkeypatch.setattr(projection, "_lista_segura", fake_lista)
    registro = projection.carregar_oportunidades_enriquecidas()[0]

    assert registro["equipamentos"] == ["SUPRA 750", "SUPRA 1150", "SUPRA 850"]
    assert registro["equipamento"] == "SUPRA 750, SUPRA 1150, SUPRA 850"
    assert registro["linhas_equipamentos"] == ["DIESEL TRUCK"]
    assert registro["familias"] == ["diesel-truck"]
    assert registro["quantidade_total"] == 14
    assert registro["cliente_nome"] == "PRIME CARGO LOGISTICA INTEGRADA LTDA"
    assert registro["municipio"] == "BARUERI"
    assert registro["estado"] == "SP"
    assert registro["ddd"] == "11"


def test_mapa_crm_rankeia_equipamentos_sem_inflar_negociacoes():
    camada = _camada_crm([
        {"status": "PROPOSTA", "valor_estimado": 100, "equipamentos": ["SUPRA 750", "SUPRA 1150"], "estado": "SP", "municipio": "BARUERI", "ddd": "11"},
        {"status": "PROPOSTA", "valor_estimado": 200, "equipamentos": ["SUPRA 1150"], "estado": "SP", "municipio": "SAO PAULO", "ddd": "11"},
        {"status": "GANHO", "valor_estimado": 300, "equipamentos": ["CITIMAX 400"], "estado": "SP", "municipio": "SAO PAULO", "ddd": "11"},
    ])

    assert camada["total_registros"] == 2
    assert camada["valor_pipeline"] == 300
    assert camada["equipamentos"] == [
        {"nome": "SUPRA 1150", "quantidade_registros": 2},
        {"nome": "SUPRA 750", "quantidade_registros": 1},
    ]


def test_drilldown_crm_encontra_equipamento_em_lista():
    registro = {"equipamentos": ["SUPRA 750", "SUPRA 1150"], "equipamento": "SUPRA 750, SUPRA 1150"}
    assert _corresponde(registro, ("equipamentos", "equipamento"), "SUPRA 1150") is True
    assert _corresponde(registro, ("equipamentos", "equipamento"), "CITIMAX 400") is False
