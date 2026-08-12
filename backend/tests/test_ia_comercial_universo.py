from services import ia_comercial_universo as universo


def _fontes_fake():
    return {
        "historico_anfir": [
            {"implementadora": "IBIPORA", "fabricante_equipamento": "CARRIER", "cliente": "A", "valor": 10},
            {"implementadora": "IBIPORA", "fabricante_equipamento": "THERMO KING", "cliente": "B", "valor": 20},
            {"implementadora": "PAVAN", "fabricante_equipamento": "CARRIER", "cliente": "C", "valor": 30},
        ],
        "clientes": [{"id": "c1", "nome": "Cliente A"}],
        "oportunidades": [],
        "itens_oportunidade": [],
        "propostas": [],
        "aceites": [],
        "pedidos": [],
        "atividades": [],
        "vendas": [],
        "implementadoras_cadastro": [
            {"id": "i1", "nome": "IBIPORA", "ativo": True},
            {"id": "i2", "nome": "PAVAN", "ativo": True},
        ],
        "catalogo_produtos": [{"code": "TR", "modelo_canonical_name": "X4-7500"}],
        "perfil_usuario": [{"id": "u1", "tipo_usuario": "ADMIN_MASTER"}],
    }


def test_catalogo_descobre_campos_dinamicamente(monkeypatch):
    monkeypatch.setattr(universo, "_carregar_fontes", lambda usuario_id, tipo_usuario: (_fontes_fake(), {"escopo_territorial": {"modo": "global"}}))

    catalogo = universo.catalogar_universo_cti("u1", "ADMIN_MASTER")
    historico = next(item for item in catalogo["fontes"] if item["fonte"] == "historico_anfir")

    assert historico["total_registros_autorizados"] == 3
    assert "implementadora" in historico["campos_disponiveis"]
    assert "fabricante_equipamento" in historico["campos_disponiveis"]


def test_consulta_universal_faz_ranking_sem_regra_especifica_de_implementadora(monkeypatch):
    monkeypatch.setattr(universo, "_carregar_fontes", lambda usuario_id, tipo_usuario: (_fontes_fake(), {"escopo_territorial": {"modo": "global"}}))

    resultado = universo.consultar_universo_cti(
        "u1",
        "ADMIN_MASTER",
        fonte="historico_anfir",
        agrupar_por=["implementadora"],
        metricas=[{"operacao": "count", "campo": None, "alias": "quantidade"}],
        ordenar_por="quantidade",
        direcao="desc",
        limite=10,
    )

    assert resultado["resultado"][0] == {"implementadora": "IBIPORA", "quantidade": 2}
    assert resultado["resultado"][1] == {"implementadora": "PAVAN", "quantidade": 1}


def test_consulta_universal_nao_confunde_implementadora_com_fabricante(monkeypatch):
    monkeypatch.setattr(universo, "_carregar_fontes", lambda usuario_id, tipo_usuario: (_fontes_fake(), {"escopo_territorial": {"modo": "global"}}))

    por_implementadora = universo.consultar_universo_cti(
        "u1", "ADMIN_MASTER", fonte="historico_anfir",
        agrupar_por=["implementadora"],
        metricas=[{"operacao": "count", "campo": None, "alias": "quantidade"}],
        ordenar_por="quantidade", direcao="desc",
    )
    por_fabricante = universo.consultar_universo_cti(
        "u1", "ADMIN_MASTER", fonte="historico_anfir",
        agrupar_por=["fabricante_equipamento"],
        metricas=[{"operacao": "count", "campo": None, "alias": "quantidade"}],
        ordenar_por="quantidade", direcao="desc",
    )

    assert por_implementadora["resultado"][0]["implementadora"] == "IBIPORA"
    assert por_fabricante["resultado"][0]["fabricante_equipamento"] == "CARRIER"


def test_consulta_universal_aplica_filtros_e_metricas_genericas(monkeypatch):
    monkeypatch.setattr(universo, "_carregar_fontes", lambda usuario_id, tipo_usuario: (_fontes_fake(), {"escopo_territorial": {"modo": "global"}}))

    resultado = universo.consultar_universo_cti(
        "u1", "ADMIN_MASTER", fonte="historico_anfir",
        filtros=[{"campo": "fabricante_equipamento", "operador": "eq", "valor": "CARRIER"}],
        agrupar_por=["implementadora"],
        metricas=[{"operacao": "sum", "campo": "valor", "alias": "valor_total"}],
        ordenar_por="valor_total", direcao="desc",
    )

    assert resultado["total_filtrado"] == 2
    assert resultado["resultado"][0] == {"implementadora": "PAVAN", "valor_total": 30.0}


def test_fonte_inexistente_e_recusada(monkeypatch):
    monkeypatch.setattr(universo, "_carregar_fontes", lambda usuario_id, tipo_usuario: (_fontes_fake(), {}))

    resultado = universo.consultar_universo_cti("u1", "ADMIN_MASTER", fonte="secrets")

    assert "erro" in resultado
    assert "secrets" not in resultado["fontes_disponiveis"]
