from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "ia_comercial_mapa_router.py"
SERVICE = ROOT / "frontend" / "src" / "services" / "mapa-equipe-api.ts"
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"


def test_fluxo_contextual_esta_conectado_fim_a_fim():
    router = ROUTER.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    mapa = MAPA.read_text(encoding="utf-8")
    assert '@router.post("/inteligencia/perguntar")' in router
    assert "perguntarMapaEquipeInteligencia" in service
    assert "perguntarMapaEquipeInteligencia" in mapa
