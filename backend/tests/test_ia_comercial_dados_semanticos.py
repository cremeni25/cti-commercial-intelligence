from services import ia_comercial_agente as agente
from services import ia_comercial_dados_semanticos as dados


def test_consulta_semantica_nao_limita_base_a_120(monkeypatch):
    oportunidades = [
        {"id": f"opp-{i}", "responsavel_id": "user-1", "cliente_id": f"cli-{i}", "status": "ABERTA"}
        for i in range(250)
    ]
    clientes = [{"id": f"cli-{i}", "nome": f"Cliente {i}"} for i in range(250)]

    def fake_carregar(dominio):
        if dominio == "oportunidades":
            return oportunidades
        if dominio == "clientes":
            return clientes
        return []

    monkeypatch.setattr(dados, "_carregar_dominio", fake_carregar)

    primeira = dados.consultar_dominio_semantico(
        "oportunidades", "admin", "ADMIN_MASTER", limite=100, offset=0
    )
    terceira = dados.consultar_dominio_semantico(
        "oportunidades", "admin", "ADMIN_MASTER", limite=100, offset=200
    )

    assert primeira["total_encontrado"] == 250
    assert len(primeira["resultado"]) == 100
    assert primeira["tem_mais"] is True
    assert len(terceira["resultado"]) == 50
    assert terceira["tem_mais"] is False


def test_consulta_semantica_filtra_status_no_conjunto_completo(monkeypatch):
    oportunidades = [
        {"id": "1", "status": "GANHO"},
        {"id": "2", "status": "ABERTA"},
        {"id": "3", "status": "GANHO"},
    ]

    monkeypatch.setattr(
        dados,
        "_carregar_dominio",
        lambda dominio: oportunidades if dominio == "oportunidades" else [],
    )

    resultado = dados.consultar_dominio_semantico(
        "oportunidades", "admin", "ADMIN_MASTER", status="ganho", limite=100
    )

    assert resultado["total_encontrado"] == 2
    assert {item["id"] for item in resultado["resultado"]} == {"1", "3"}


def test_catalogo_agente_expoe_vendas_e_paginacao_sem_sql_generico():
    ferramenta = next(
        item
        for item in agente.ferramentas_agente()
        if item.get("name") == "consultar_dominio_cti"
    )
    propriedades = ferramenta["parameters"]["properties"]
    dominios = propriedades["dominio"]["enum"]

    assert "vendas" in dominios
    assert "offset" in propriedades
    assert "status" in propriedades
    assert "sql" not in propriedades
    assert "tabela" not in propriedades
    assert "query" not in propriedades


def test_vendas_respeitam_escopo_por_oportunidade_ou_cliente(monkeypatch):
    registros = {
        "oportunidades": [
            {"id": "opp-user", "responsavel_id": "user-1", "cliente_id": "cli-user"},
            {"id": "opp-other", "responsavel_id": "user-2", "cliente_id": "cli-other"},
        ],
        "clientes": [
            {"id": "cli-user", "nome": "Cliente User"},
            {"id": "cli-other", "nome": "Cliente Other"},
        ],
        "vendas": [
            {"id": "v1", "oportunidade_id": "opp-user", "cliente_id": "cli-user"},
            {"id": "v2", "oportunidade_id": "opp-other", "cliente_id": "cli-other"},
        ],
    }
    monkeypatch.setattr(dados, "_carregar_dominio", lambda dominio: registros.get(dominio, []))

    resultado = dados.consultar_dominio_semantico(
        "vendas", "user-1", "VENDEDOR", limite=100
    )

    assert resultado["total_encontrado"] == 1
    assert resultado["resultado"][0]["id"] == "v1"
