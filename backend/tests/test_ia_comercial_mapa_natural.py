from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "backend/api.py"
ROUTER = ROOT / "backend/routers/ia_comercial_mapa_router.py"
SERVICE = ROOT / "frontend/src/services/mapa-equipe-api.ts"
MAPA = ROOT / "frontend/src/app/mapa-estrategico/page.tsx"


def test_router_de_inteligencia_contextual_do_mapa_esta_registrado():
    api = API.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    assert "ia_comercial_mapa_router" in api
    assert "router.include_router(ia_comercial_mapa_router)" in api
    assert 'prefix="/crm-seguro/mapa-equipe"' in router
    assert '@router.get("/inteligencia")' in router
    assert '@router.post("/inteligencia/perguntar")' in router


def test_inteligencia_do_mapa_reusa_contexto_sem_criar_novo_botao_de_ia():
    api = API.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    mapa = MAPA.read_text(encoding="utf-8")
    assert "ia_comercial_mapa_router" in api
    assert "router.include_router(ia_comercial_mapa_router)" in api
    assert "getMapaEquipeInteligencia" in service
    assert "perguntarMapaEquipeInteligencia" in service
    assert "crm-seguro/mapa-equipe/inteligencia/perguntar" in service
    assert "getMapaEquipeInteligencia" not in mapa
    assert "perguntarMapaEquipeInteligencia" not in mapa
    assert "historicoContextual" not in mapa


def test_mapa_prioriza_graficos_e_acao_comercial_em_2026():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Mercado total → retiradas → mercado real Viena" in mapa
    assert "Composição por linha" in mapa
    assert "Caminho comercial" in mapa
    assert "Mercado sem CRM" in mapa
    assert "GraficoLinha" in mapa
    assert "Leitura comercial" in mapa
    assert "O que fazer" in mapa
    assert "Perdas comerciais · ANFIR 2026" in mapa
    assert "Evolução por linha · ANFIR 2026" in mapa
    assert "Histórico comercial 2023–2026" not in mapa
    assert "Dados de apoio e auditoria" in mapa
