from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "crm_scope_mapa_equipe_router.py"
PAGE = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"
SERVICE = ROOT / "frontend" / "src" / "services" / "mapa-equipe-api.ts"


def test_backend_expoe_fechamento_macro_micro_e_reconciliacao():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert '"participacoes_equipe"' in fonte
    assert '"soma_mercado_individual"' in fonte
    assert '"sobreposicoes_entre_carteiras"' in fonte
    assert '"mercado_real_sem_carteira"' in fonte
    assert '"reconciliacao"' in fonte
    assert '"nas_tres_fontes"' in fonte
    assert '"historico_fora_mercado_real"' in fonte
    assert '"crm_fora_mercado_real"' in fonte


def test_frontend_explica_fechamento_e_fontes_sem_misturar_grandezas():
    page = PAGE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    assert "Fechamento macro = micro" in page
    assert "Participação real da equipe no Mercado Real Viena" in page
    assert "Conciliação das três fontes" in page
    assert "Mesmo cliente · mesmo responsável · mesmo recorte" in page
    assert "Eventos comerciais do mesmo recorte" in page
    assert "participacoes_equipe" in service
    assert "soma_mercado_individual" in service
    assert "sobreposicoes_entre_carteiras" in service
    assert "mercado_real_sem_carteira" in service
