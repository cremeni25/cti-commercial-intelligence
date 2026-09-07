from pathlib import Path

from core.admin_auth import UsuarioAutenticado
from routers import crm_scope_mapa_equipe_router as mapa

ROOT = Path(__file__).resolve().parents[2]
INSIGHTS = ROOT / "backend" / "routers" / "crm_scope_mapa_insights_router.py"
PAGE = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"
SERVICE = ROOT / "frontend" / "src" / "services" / "mapa-equipe-api.ts"


def _usuario(tipo: str = "REPRES_REGIAO_01", user_id: str = "u1") -> UsuarioAutenticado:
    return UsuarioAutenticado(
        id=user_id,
        auth_id="auth",
        email="teste@cti.local",
        nome="Usuário Teste",
        tipo_usuario=tipo,
        permissoes={},
    )


def test_usuario_comercial_nao_master_ignora_responsavel_solicitado(monkeypatch):
    monkeypatch.setattr(mapa, "_equipe_ativa", lambda: [
        {"id": "u1", "nome": "Usuário Teste", "tipo_usuario": "REPRES_REGIAO_01"},
        {"id": "u2", "nome": "Outro Usuário", "tipo_usuario": "REPRES_REGIAO_02"},
    ])
    usuario = _usuario()
    alvo, equipe = mapa._resolver_alvo(usuario, "u2")
    assert alvo is usuario
    assert [item["id"] for item in equipe] == ["u1"]


def test_master_pode_consolidar_sem_responsavel(monkeypatch):
    monkeypatch.setattr(mapa, "_equipe_ativa", lambda: [
        {"id": "u1", "nome": "Usuário 1", "tipo_usuario": "REPRES_REGIAO_01"},
        {"id": "u2", "nome": "Usuário 2", "tipo_usuario": "REPRES_REGIAO_02"},
    ])
    alvo, equipe = mapa._resolver_alvo(_usuario("ADMIN_MASTER", "master"), None)
    assert alvo is None
    assert len(equipe) == 2


def test_mapa_tem_tres_caminhos_de_inteligencia_e_preserva_escopo():
    page = PAGE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    insights = INSIGHTS.read_text(encoding="utf-8")
    assert "Inteligência de regiões" in page
    assert "Evolução por linha" in page
    assert "Onde perdemos e por quê" in page
    assert "getMapaInsights" in service
    assert '"consolidado": consolidado' in insights
    assert "DEMAIS_USUARIOS_SEMPRE_RECEBEM_APENAS_O_PROPRIO_LOGIN" in insights
    assert "if (!dados?.pode_selecionar_responsavel)" in page
    assert "setMercadoMacro(null)" in page
