from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "frontend/src/services/modulos-api.ts"
TEAM_SERVICE = ROOT / "frontend/src/services/mapa-equipe-api.ts"
EQUIPMENT = ROOT / "frontend/src/components/EquipamentoEstrategicoPage.tsx"
MAP = ROOT / "frontend/src/app/mapa-estrategico/page.tsx"
STRATEGIC_I18N = ROOT / "frontend/src/core/i18n/strategic.ts"


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
    assert "fetchMapaComTimeout" in team_service
    assert 'crm-seguro/mapa-equipe/visao?' in team_service
    assert 'crm-seguro/mapa-equipe/insights' in team_service
    assert 'crm-seguro/mapa-equipe/detalhamento?' in team_service
    assert "getMapaEquipeVisao" in mapa
    assert "getMapaInsights" in mapa
    assert "Responsável comercial" in mapa
    assert "Mercado total → retiradas → mercado real Viena" in mapa
    assert "Composição por linha" in mapa
    assert "Caminho comercial" in mapa
    assert "Leitura comercial" in mapa
    assert "O que fazer" in mapa
