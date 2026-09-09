from types import SimpleNamespace

from routers import crm_scope_mapa_insights_router as insights
from services.mapa_perdas_direcionamento import direcionar_registros


def test_direcionamento_preserva_cliente_ocorrencias_e_unidades():
    registros = [
        {"cliente": "CLIENTE A", "responsavel": "ANDRÉ", "linha": "DD", "quantidade": 2},
        {"cliente": "CLIENTE A", "responsavel": "ANDRÉ", "linha": "DD", "quantidade": 3},
        {"cliente": "CLIENTE B", "responsavel": "MÔNICA", "linha": "TR", "quantidade": 4},
    ]
    resultado = direcionar_registros(registros, insights._quantidade, insights._linha_nome)
    assert resultado["alvos"][0]["cliente"] == "CLIENTE A"
    assert resultado["alvos"][0]["unidades"] == 5
    assert resultado["alvos"][0]["ocorrencias"] == 2
    assert "ANDRÉ → CLIENTE A" in resultado["texto"]


def test_regiao_prioriza_cliente_anfir_sem_crm_ativo(monkeypatch):
    responsavel = SimpleNamespace(id="u1", nome="ANDRÉ")
    equipe = [{"id": "u1", "nome": "ANDRÉ", "tipo_usuario": "REPRES_REGIAO_01", "ddds": []}]
    mercado = [
        {"ano": 2026, "mes": 1, "responsavel": "ANDRÉ", "cliente": "CLIENTE COM CRM", "linha": "DD", "quantidade": 2},
        {"ano": 2026, "mes": 2, "responsavel": "ANDRÉ", "cliente": "CLIENTE SEM CRM", "linha": "DD", "quantidade": 5},
    ]
    crm = [{"ano": 2026, "cliente": "CLIENTE COM CRM", "status": "ABERTO", "valor_estimado": 1000}]

    monkeypatch.setattr(insights, "_usuario_regional", lambda _registro: responsavel)
    monkeypatch.setattr(insights, "filtrar_anfir_por_responsavel_comercial", lambda registros, _id, _nome: registros)
    monkeypatch.setattr(insights, "carregar_oportunidades_enriquecidas", lambda: crm)
    monkeypatch.setattr(insights, "_crm_carteira", lambda _responsavel, base: base)
    monkeypatch.setattr(insights, "_clientes_carteira_atual", lambda _id: 2)

    resultado = insights._regioes(responsavel, equipe, mercado)[0]
    assert resultado["mercado_2026"] == 7
    assert resultado["crm_ativos"] == 1
    assert resultado["direcionamento"]["alvos"][0]["cliente"] == "CLIENTE SEM CRM"
    assert "Prioridade sem CRM ativo" in resultado["acao_recomendada"]
    assert "ANDRÉ → CLIENTE SEM CRM" in resultado["acao_recomendada"]


def test_linha_prioriza_movimento_fora_da_captura_carrier(monkeypatch):
    monkeypatch.setattr(insights, "composicao_marca_linha", lambda registros: {
        "mercado": sum(insights._quantidade(item, 1) for item in registros),
        "carrier": 2,
        "outras_marcas": 5,
        "marca_nao_discriminada": 0,
        "carrier_pct": 28.57,
        "outras_marcas_pct": 71.43,
        "marca_nao_discriminada_pct": 0,
        "fechamento_total": 7,
        "fechamento_ok": True,
        "marcas_concorrentes": [],
        "regra": "TESTE",
    })
    base = [
        {"ano": 2026, "mes": 1, "responsavel": "ANDRÉ", "cliente": "CLIENTE CARRIER", "linha": "TR", "quantidade": 2, "status": "Carrier"},
        {"ano": 2026, "mes": 2, "responsavel": "ANDRÉ", "cliente": "CLIENTE TK", "linha": "TR", "quantidade": 5, "status": "TK"},
    ]
    resultado = insights._linhas_2026(base)["linhas"][0]
    assert resultado["total_2026"] == 7
    assert resultado["direcionamento"]["alvos"][0]["cliente"] == "CLIENTE TK"
    assert "Prioridade comercial fora da captura Carrier" in resultado["acao_recomendada"]
    assert "ANDRÉ → CLIENTE TK" in resultado["acao_recomendada"]
