from core.admin_auth import UsuarioAutenticado
from routers import crm_scope_mapa_insights_router as insights


def _usuario(user_id: str = "u1") -> UsuarioAutenticado:
    return UsuarioAutenticado(
        id=user_id,
        auth_id="auth",
        email="teste@cti.local",
        nome="Usuario Teste",
        tipo_usuario="REPRES_REGIAO_01",
        permissoes={},
    )


def test_regiao_separa_cliente_negociacao_e_unidade(monkeypatch):
    monkeypatch.setattr(insights, "carregar_oportunidades_enriquecidas", lambda: [])
    monkeypatch.setattr(insights, "filtrar_anfir_por_responsavel_comercial", lambda registros, *_: registros)
    monkeypatch.setattr(insights, "_clientes_carteira_atual", lambda _id: 7)
    equipe = [{"id": "u1", "nome": "Usuario Teste", "tipo_usuario": "REPRES_REGIAO_01", "ddds": []}]
    base = [
        {"ano": 2026, "mes": 1, "quantidade": 2, "cliente": "CLIENTE A"},
        {"ano": 2026, "mes": 1, "quantidade": 1, "cliente": "CLIENTE A"},
        {"ano": 2026, "mes": 2, "quantidade": 3, "cliente": "CLIENTE B"},
    ]
    item = insights._regioes(_usuario(), equipe, base)[0]
    assert item["mercado_2026"] == 6
    assert item["mercado_mensal"][:2] == [3, 3]
    assert item["clientes_anfir_2026"] == 2
    assert item["negociacoes_anfir_2026"] == 3
    assert item["clientes_carteira"] == 7
    assert item["clientes_mercado"] == 2


def test_mesma_empresa_repetida_dez_vezes_conta_um_cliente_e_dez_negociacoes(monkeypatch):
    monkeypatch.setattr(insights, "carregar_oportunidades_enriquecidas", lambda: [])
    monkeypatch.setattr(insights, "filtrar_anfir_por_responsavel_comercial", lambda registros, *_: registros)
    monkeypatch.setattr(insights, "_clientes_carteira_atual", lambda _id: 0)
    equipe = [{"id": "u1", "nome": "Usuario Teste", "tipo_usuario": "REPRES_REGIAO_01", "ddds": []}]
    base = [{"ano": 2026, "mes": 3, "quantidade": 1, "cliente": "MESMO CLIENTE"} for _ in range(10)]
    item = insights._regioes(_usuario(), equipe, base)[0]
    assert item["clientes_anfir_2026"] == 1
    assert item["negociacoes_anfir_2026"] == 10
    assert item["mercado_2026"] == 10


def test_regiao_filtra_crm_para_2026(monkeypatch):
    crm = [
        {"responsavel_id": "u1", "status": "ABERTO", "valor_estimado": 100, "data_abertura": "2025-12-20"},
        {"responsavel_id": "u1", "status": "ABERTO", "valor_estimado": 200, "data_abertura": "2026-02-10"},
        {"responsavel_id": "u1", "status": "GANHO", "valor_estimado": 300, "data_abertura": "2026-03-10"},
    ]
    monkeypatch.setattr(insights, "carregar_oportunidades_enriquecidas", lambda: crm)
    monkeypatch.setattr(insights, "_crm_carteira", lambda _u, registros: registros)
    monkeypatch.setattr(insights, "filtrar_anfir_por_responsavel_comercial", lambda registros, *_: registros)
    monkeypatch.setattr(insights, "_clientes_carteira_atual", lambda _id: 1)
    equipe = [{"id": "u1", "nome": "Usuario Teste", "tipo_usuario": "REPRES_REGIAO_01", "ddds": []}]
    item = insights._regioes(_usuario(), equipe, [{"ano": 2026, "mes": 1, "quantidade": 1, "cliente": "A"}])[0]
    assert item["crm_registros_2026"] == 2
    assert item["crm_ativos"] == 1
    assert item["pipeline_ativo"] == 200.0


def test_ano_registro_reconhece_data_abertura_crm():
    assert insights._ano_registro({"data_abertura": "2026-05-01T00:00:00"}) == 2026
