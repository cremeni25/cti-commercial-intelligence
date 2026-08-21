from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VENDAS_ROUTER = ROOT / "backend" / "routers" / "vendas_router.py"
TESTES_ARQUIVADOS = ROOT / "frontend" / "src" / "app" / "crm-app" / "testes-arquivados" / "page.tsx"


def test_listagem_operacional_de_vendas_exclui_testes_arquivados():
    fonte = VENDAS_ROUTER.read_text(encoding="utf-8")

    assert '.or_("registro_teste.is.null,registro_teste.eq.false")' in fonte
    assert '.is_("arquivado_em", "null")' in fonte


def test_tela_de_testes_arquivados_encaminha_token_da_sessao():
    fonte = TESTES_ARQUIVADOS.read_text(encoding="utf-8")

    assert 'getSupabaseClient' in fonte
    assert 'headers.set("Authorization", `Bearer ${data.session.access_token}`)' in fonte
    assert 'fetchProtegido("/api/crm-proxy/crm-app/oportunidades/testes-arquivados"' in fonte
    assert 'fetchProtegido(`/api/crm-proxy/crm-app/oportunidades/${encodeURIComponent(id)}/restaurar-teste`' in fonte
