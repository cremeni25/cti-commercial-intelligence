from services import ia_comercial_agente as agente
from services import ia_comercial_territorio_anfir as territorial


def _base():
    return [
        {"cliente": "A", "estado": "SP", "cidade": "São Paulo", "ddd": "11", "linha": "TR", "modelo": "X4-7500", "valor": 100.0, "quantidade": 1, "origem_dado": "BRASIL"},
        {"cliente": "B", "estado": "SP", "cidade": "Campinas", "ddd": "19", "linha": "DT", "modelo": "SUPRA 850", "valor": 200.0, "quantidade": 1, "origem_dado": "BRASIL"},
        {"cliente": "C", "estado": "SP", "cidade": "Santos", "ddd": "13", "linha": "TR", "modelo": "VECTOR HE19", "valor": 300.0, "quantidade": 2, "origem_dado": "BRASIL"},
    ]


def test_master_tem_escopo_global(monkeypatch):
    monkeypatch.setattr(territorial.repository, "buscar_cti_anfir", _base)

    resultado = territorial.consultar_territorio_semantico(
        "u-master",
        "ADMIN_MASTER",
        limite=100,
        offset=0,
    )

    assert resultado["erro"] if "erro" in resultado else None is None
    assert resultado["escopo"]["modo"] == "global"
    assert resultado["total_encontrado"] == 3
    assert resultado["resumo"]["total_clientes"] == 3


def test_usuario_com_ddds_so_enxerga_territorio_autorizado(monkeypatch):
    monkeypatch.setattr(territorial.repository, "buscar_cti_anfir", _base)
    monkeypatch.setattr(
        territorial,
        "_consulta_segura",
        lambda tabela: (
            [{"id": "u1", "tipo_usuario": "USUARIO_CTI", "territorio": "Viena SP", "ddds": ["011", "013"]}]
            if tabela == "cti_users"
            else []
        ),
    )

    resultado = territorial.consultar_anfir_semantico(
        "u1",
        "USUARIO_CTI",
        limite=100,
        offset=0,
    )

    assert resultado["escopo"]["ddds_autorizados"] == ["011", "013"]
    assert resultado["total_encontrado"] == 2
    assert {item["ddd"] for item in resultado["resultado"]} == {"011", "013"}


def test_ddd_fora_do_escopo_e_recusado(monkeypatch):
    monkeypatch.setattr(territorial.repository, "buscar_cti_anfir", _base)
    monkeypatch.setattr(
        territorial,
        "_consulta_segura",
        lambda tabela: ([{"id": "u1", "ddds": ["011"]}] if tabela == "cti_users" else []),
    )

    resultado = territorial.consultar_territorio_semantico(
        "u1",
        "USUARIO_CTI",
        ddd="019",
        limite=10,
        offset=0,
    )

    assert "fora do escopo autorizado" in resultado["erro"]
    assert resultado["total_encontrado"] == 0


def test_resumo_usa_todo_recorte_e_pagina_so_detalha(monkeypatch):
    monkeypatch.setattr(territorial.repository, "buscar_cti_anfir", _base)

    resultado = territorial.consultar_territorio_semantico(
        "u-master",
        "ADMIN_MASTER",
        uf="SP",
        limite=1,
        offset=0,
    )

    assert resultado["total_encontrado"] == 3
    assert resultado["resumo"]["total_registros"] == 3
    assert len(resultado["resultado"]) == 1
    assert resultado["tem_mais"] is True


def test_gate_distingue_territorio_e_anfir():
    requeridas = agente._fontes_requeridas(
        "Compare o DDD 011 com a ANFIR para a linha Trailer."
    )

    assert "territorio" in requeridas
    assert "anfir" in requeridas
    assert "produtos" in requeridas


def test_catalogo_agente_expoe_novas_primitivas_sem_acesso_admin():
    ferramentas = agente.ferramentas_agente()
    nomes = {item.get("name") for item in ferramentas if item.get("type") == "function"}

    assert "consultar_territorio_cti" in nomes
    assert "consultar_anfir_cti" in nomes
    assert "sql" not in " ".join(sorted(nomes)).casefold()
    assert nomes == agente.FERRAMENTAS_CTI_PERMITIDAS
