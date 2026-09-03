from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "strategic_layers_router.py"
SECURE_ROUTER = ROOT / "backend" / "routers" / "crm_scope_estrategia_router.py"
TEAM_ROUTER = ROOT / "backend" / "routers" / "crm_scope_mapa_equipe_router.py"
MAIN = ROOT / "backend" / "main.py"
SERVICE = ROOT / "frontend" / "src" / "services" / "modulos-api.ts"
TEAM_SERVICE = ROOT / "frontend" / "src" / "services" / "mapa-equipe-api.ts"
EQUIPMENT = ROOT / "frontend" / "src" / "components" / "EquipamentoPage.tsx"
MAP = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"
STRATEGIC_I18N = ROOT / "frontend" / "src" / "core" / "i18n" / "strategic.ts"


def test_router_preserva_tres_camadas_sem_fusao():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert '@router.get("/equipamentos/{slug}")' in fonte
    assert '@router.get("/mapa")' in fonte
    assert '"regra": "CAMADAS_SEPARADAS_SEM_FUSAO"' in fonte
    assert '"regra": "CORRELACAO_SEM_FUSAO"' in fonte
    assert 'carregar_historico_comercial()' in fonte
    assert 'carregar_oportunidades_enriquecidas()' in fonte
    assert 'fonte_anfir()' in fonte


def test_classificacao_reconhece_codigos_canonicos_tr_dt_dd():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert '"TR": "trailer"' in fonte
    assert '"DT": "diesel-truck"' in fonte
    assert '"DD": "direct-drive"' in fonte
    assert '_codigo_familia(registro.get("linha"))' in fonte
    assert '_codigo_familia(registro.get("linha_equipamentos"))' in fonte


def test_router_estrategico_esta_registrado_no_backend():
    fonte = MAIN.read_text(encoding="utf-8")
    seguro = SECURE_ROUTER.read_text(encoding="utf-8")
    equipe = TEAM_ROUTER.read_text(encoding="utf-8")
    assert "strategic_layers_router" in fonte
    assert "app.include_router(strategic_layers_router)" in fonte
    assert "crm_scope_estrategia_router" in fonte
    assert "app.include_router(crm_scope_estrategia_router)" in fonte
    assert 'prefix="/crm-seguro/estrategia"' in seguro
    assert "crm_scope_mapa_equipe_router" in fonte
    assert "app.include_router(crm_scope_mapa_equipe_router)" in fonte
    assert 'prefix="/crm-seguro/mapa-equipe"' in equipe
    assert '@router.get("/visao")' in equipe


def test_frontend_consume_projecao_estrategica_real_autenticada():
    service = SERVICE.read_text(encoding="utf-8")
    team_service = TEAM_SERVICE.read_text(encoding="utf-8")
    equipment = EQUIPMENT.read_text(encoding="utf-8")
    mapa = MAP.read_text(encoding="utf-8")
    catalogo = STRATEGIC_I18N.read_text(encoding="utf-8")

    assert 'fetchCrmSeguroProxy(`crm-seguro/estrategia/${caminho}`' in service
    assert '`equipamentos/${slug}?${normalizarQuery(query)}`' in service
    assert '`mapa?${normalizarQuery(query)}`' in service
    assert 't("equipment.realized")' in equipment
    assert 't("equipment.history")' in equipment
    assert 't("equipment.live")' in equipment
    assert "REALIZADO · ANFIR" in catalogo
    assert "COMPLETED · ANFIR" in catalogo
    assert 'fetchCrmSeguroProxy(`crm-seguro/mapa-equipe/visao?' in team_service
    assert "getMapaEquipeVisao" in mapa
    assert "Região / responsável" in mapa
    assert "GraficoPizzaParticipacao" in mapa
    assert "GraficoPizzaFamilias" in mapa
    assert "Cliente a cliente · evidências encontradas" in mapa
    assert "A correlação é estratégica, não uma fusão de registros." in catalogo
