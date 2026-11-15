"""Setorização da carteira e ficha única por empresa (dados fictícios)."""
from datetime import date, timedelta

import pytest

from services import carteira_setorizada as carteira
from tests import supabase_memoria

HOJE = date.today()


def _dias(n):
    return (HOJE - timedelta(days=n)).isoformat()


@pytest.fixture
def base(monkeypatch):
    dados = {
        "cti_users": [{"id": "ana", "nome": "Ana", "ativo": True}, {"id": "beto", "nome": "Beto", "ativo": True}],
        "clientes": [
            {"id": "ativo", "nome": "Frios Alfa Ltda", "cnpj": "11.111.111/0001-11", "responsavel_comercial_id": "ana", "segmento": "FRIGORIFICO"},
            {"id": "inativo", "nome": "Laticinios Beta", "cnpj": None, "responsavel_comercial_id": "beto"},
            {"id": "prospect-frota", "nome": "Transportes Gama", "cnpj": "33.333.333/0001-33", "responsavel_comercial_id": None},
            {"id": "prospect", "nome": "Delta Logistica", "cnpj": None, "responsavel_comercial_id": "ana"},
        ],
        "cti_oportunidades": [
            {"id": "o1", "cliente_id": "ativo", "responsavel_id": "ana", "status": "PROPOSTA", "valor_total": 50000, "arquivado_em": None},
        ],
        "cti_pedidos": [{"id": "p1", "cliente_id": "ativo", "created_at": _dias(100)}],
        "cti_atividades": [{"id": "a1", "cliente_id": "ativo", "usuario_id": "ana", "status": "REALIZADA", "data": _dias(5), "tipo": "VISITA", "titulo": "Visita"}],
        "cti_cliente_responsabilidade_historico": [{"cliente_id": "ativo", "responsavel_anterior_id": "beto", "responsavel_novo_id": "ana", "motivo": "Transferência de carteira", "created_at": _dias(30)}],
    }
    anfir = [
        *[{"cliente": "TRANSPORTES GAMA", "cnpj": "33333333000133", "quantidade": 1, "status": "TK", "implementadora": "RANDON", "data": _dias(9 * 365)} for _ in range(25)],
        {"cliente": "FRIOS ALFA LTDA", "cnpj": "11111111000111", "quantidade": 3, "status": "CARRIER", "implementadora": "FACCHINI", "data": _dias(400)},
    ]
    monkeypatch.setattr("core.supabase_client.supabase", supabase_memoria.criar(dados))
    monkeypatch.setattr("repositories.cti_repository.CTIRepository.buscar_cti_anfir", lambda self, page_size=1000: anfir)
    vendas = [{"cliente": "LATICINIOS BETA", "mes": _dias(4 * 365), "data_emissao": _dias(4 * 365), "equipamento": "CITIMAX 500", "quantidade": 2, "vendedor": "BETO"},
              {"cliente": "LATICINIOS BETA", "mes": _dias(5 * 365), "data_emissao": _dias(5 * 365), "equipamento": "CITIMAX 280", "quantidade": 1, "vendedor": "BETO"}]
    monkeypatch.setattr("services.planilhas_comerciais.registros", lambda fonte: vendas if fonte == "vendas_realizadas" else [])
    carteira.limpar_cache()
    yield dados
    carteira.limpar_cache()


def _perfil(resultado, cid):
    return next(c for c in resultado["clientes"] if c["cliente_id"] == cid)


def test_grupos_porte_e_sinais(base):
    r = carteira.setorizacao()
    assert r["total_clientes"] == 4
    assert r["por_grupo"] == {"CLIENTE_ATIVO": 1, "CLIENTE_INATIVO": 1, "PROSPECT_COM_FROTA": 1, "PROSPECT": 1}
    ativo, inativo, gama = _perfil(r, "ativo"), _perfil(r, "inativo"), _perfil(r, "prospect-frota")
    assert ativo["grupo"] == "CLIENTE_ATIVO" and ativo["porte"] == "PEQUENO" and ativo["frota_carrier"] == 3 and "NEGOCIO_ABERTO" in ativo["sinais"]
    assert inativo["grupo"] == "CLIENTE_INATIVO" and "RECORRENTE" in inativo["sinais"] and inativo["unidades_compradas"] == 3
    assert gama["grupo"] == "PROSPECT_COM_FROTA" and gama["porte"] == "GRANDE" and gama["frota_concorrencia"] == 25
    assert {"USA_CONCORRENTE", "JANELA_RENOVACAO", "SEM_RESPONSAVEL"} <= set(gama["sinais"])
    assert r["clientes"][0]["cliente_id"] == "prospect-frota"  # renovação + concorrência + frota grande primeiro


def test_filtros_e_escopo_por_responsavel(base):
    assert [c["cliente_id"] for c in carteira.setorizacao(sinal="USA_CONCORRENTE")["clientes"]] == ["prospect-frota"]
    so_ana = carteira.setorizacao(responsavel_id="ana")
    assert so_ana["total_clientes"] == 2 and {c["cliente_id"] for c in so_ana["clientes"]} == {"ativo", "prospect"}


def test_ficha_unica_junta_tudo_da_empresa(base):
    f = carteira.ficha("ativo")
    assert f["cadastro"]["cnpj"] == "11.111.111/0001-11" and f["responsavel_nome"] == "Ana"
    assert f["responsaveis_anteriores"][0] == {**f["responsaveis_anteriores"][0], "de": "Beto", "para": "Ana"}
    assert f["negocios"][0]["responsavel"] == "Ana" and f["atividades_recentes"][0]["autor"] == "Ana"
    assert f["frota_por_fabricante"]["Carrier"] == 3 and f["frota_por_implementadora"] == {"FACCHINI": 1}
    assert carteira.ficha("nao-existe") is None


def test_rotas_escopo_equipe_e_gestao(base, monkeypatch):
    from fastapi.testclient import TestClient
    from core.admin_auth import UsuarioAutenticado, usuario_atual
    from main import app

    c = TestClient(app)

    def entrar(uid, tipo, **perm):
        u = UsuarioAutenticado(id=uid, auth_id=uid, email="x@x", nome=uid, tipo_usuario=tipo, permissoes=perm)
        app.dependency_overrides[usuario_atual] = lambda: u
        monkeypatch.setattr("core.application_access.usuario_atual", lambda *a, **k: u)

    h = {"Authorization": "Bearer t"}
    try:
        entrar("ana", "REPRES_REGIAO_01", oportunidades_visualizar=True)
        r = c.get("/crm-seguro/carteira/setorizacao?responsavel_id=beto", headers=h).json()
        assert r["total_clientes"] == 2  # vendedor vê só a própria carteira, mesmo pedindo outra
        assert c.get("/crm-seguro/carteira/empresa/inativo", headers=h).status_code == 403
        assert c.get("/crm-seguro/carteira/empresa/ativo", headers=h).status_code == 200
        assert len(c.get("/crm-seguro/glossario", headers=h).json()["termos"]) >= 10
        entrar("sem", "REPRES_REGIAO_01")
        assert c.get("/crm-seguro/carteira/setorizacao", headers=h).status_code == 403
        entrar("m", "ADMIN_MASTER", acesso_total=True)
        assert c.get("/crm-seguro/carteira/setorizacao", headers=h).json()["total_clientes"] == 4
        assert c.get("/crm-seguro/carteira/empresa/inativo", headers=h).status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_glossario_traduz_sinonimos():
    from core.glossario_comercial import termo_oficial

    assert termo_oficial("vendedor") == "Responsável comercial" and termo_oficial("Oportunidade") == "Negócio" and termo_oficial("xyz") is None
