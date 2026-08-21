from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "strategic_layers_router.py"
MAIN = ROOT / "backend" / "main.py"
SERVICE = ROOT / "frontend" / "src" / "services" / "modulos-api.ts"
EQUIPMENT = ROOT / "frontend" / "src" / "components" / "EquipamentoPage.tsx"
MAP = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_router_preserva_tres_camadas_sem_fusao():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert '@router.get("/equipamentos/{slug}")' in fonte
    assert '@router.get("/mapa")' in fonte
    assert '"regra": "CAMADAS_SEPARADAS_SEM_FUSAO"' in fonte
    assert '"regra": "CORRELACAO_SEM_FUSAO"' in fonte
    assert 'carregar_historico_comercial()' in fonte
    assert '_lista_segura("cti_oportunidades")' in fonte
    assert 'repository.buscar_cti_anfir()' in fonte


def test_router_estrategico_esta_registrado_no_backend():
    fonte = MAIN.read_text(encoding="utf-8")
    assert "strategic_layers_router" in fonte
    assert "app.include_router(strategic_layers_router)" in fonte


def test_frontend_consume_projecao_estrategica_real():
    service = SERVICE.read_text(encoding="utf-8")
    equipment = EQUIPMENT.read_text(encoding="utf-8")
    mapa = MAP.read_text(encoding="utf-8")

    assert "/estrategia/equipamentos/${slug}" in service
    assert "/estrategia/mapa" in service
    assert "REALIZADO · ANFIR" in equipment
    assert "HISTÓRICO COMERCIAL" in equipment
    assert "EM CURSO · CRM" in equipment
    assert "getMapaEstrategico" in mapa
    assert "Cruzamento por família" in mapa
    assert "A correlação é estratégica, não uma fusão de registros." in mapa
