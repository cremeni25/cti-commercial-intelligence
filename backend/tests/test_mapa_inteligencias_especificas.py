from pathlib import Path

from core.admin_auth import UsuarioAutenticado
from routers import crm_scope_mapa_equipe_router as mapa
from routers import crm_scope_mapa_insights_router as insights_router
from services import commercial_client_scope as scope

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


def test_mercado_por_responsavel_nao_usa_ddd_como_fallback(monkeypatch):
    monkeypatch.setattr(scope, "_mapas_clientes", lambda: ({}, {}))
    monkeypatch.setattr(scope, "_perfil_usuario", lambda usuario_id: {"id": usuario_id, "nome": "Nathan Beljato"})
    registro_so_territorial = {"cliente": "Cliente sem responsável", "ddd": "011"}

    resultado = scope.filtrar_anfir_por_responsavel_comercial(
        [registro_so_territorial],
        "nathan-id",
        "Nathan Beljato",
    )
    assert resultado == []


def test_mercado_por_responsavel_prioriza_responsavel_comercial_do_cliente(monkeypatch):
    cliente = {"nome": "Cliente A", "responsavel_comercial_id": "monica-id"}
    monkeypatch.setattr(scope, "_mapas_clientes", lambda: ({scope._fold("Cliente A"): cliente}, {}))
    monkeypatch.setattr(scope, "_perfil_usuario", lambda usuario_id: {"id": usuario_id, "nome": "Monica Almeida" if usuario_id == "monica-id" else "Nathan Beljato"})
    registro = {"cliente": "Cliente A", "ddd": "011"}

    assert scope.filtrar_anfir_por_responsavel_comercial([registro], "nathan-id", "Nathan Beljato") == []
    assert scope.filtrar_anfir_por_responsavel_comercial([registro], "monica-id", "Monica Almeida") == [registro]


def test_mapa_tem_tres_caminhos_com_graficos_e_acao_2026():
    page = PAGE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    insights = INSIGHTS.read_text(encoding="utf-8")

    assert "Inteligência de regiões" in page
    assert "Evolução por linha" in page
    assert "Onde perdemos e por quê" in page
    assert "GraficoLinha" in page
    assert "Leitura comercial" in page
    assert "O que fazer" in page
    assert "Histórico comercial 2023–2026" not in page
    assert "getMapaEquipeInteligencia" not in page
    assert "perguntarMapaEquipeInteligencia" not in page
    assert "Fatos externos verificados" not in page
    assert "linhas_2026" in service
    assert '"ano": 2026' in insights
    assert '"consolidado": consolidado' in insights
    assert "DEMAIS_USUARIOS_SEMPRE_RECEBEM_APENAS_O_PROPRIO_LOGIN" in insights
    assert "if (!dados?.pode_selecionar_responsavel) return" in page
    assert "mercadoMacro={consolidado ? mercadoMacro : null}" in page
    assert "filtrar_anfir_por_responsavel_comercial" in insights
    assert '"fonte": "ANFIR_2026"' in insights
    assert "HISTORICO_FUNIL_2026" not in insights


def test_perdas_e_linhas_operacionais_usam_somente_anfir_2026():
    anfir = [
        {"ano": 2025, "mes": 12, "status": "TK", "motivo": "Preço carrier mais alto", "linha": "TR", "quantidade": 9},
        {"ano": 2026, "mes": 1, "status": "TK", "motivo": "Preço carrier mais alto", "linha": "TR", "quantidade": 2},
        {"ano": 2026, "mes": 2, "status": "Carrier", "motivo": "", "linha": "DT", "quantidade": 3},
        {"ano": 2026, "mes": 3, "status": "Nãoédessaregião", "motivo": "", "linha": "DD", "quantidade": 1},
    ]

    perdas = insights_router._perdas_2026(anfir)
    linhas = insights_router._linhas_2026(anfir)

    assert perdas["fonte"] == "ANFIR_2026"
    assert perdas["total_perdido"] == 1
    assert perdas["mensal"][0] == 1
    assert perdas["motivos"][0]["nome"] == "Preço carrier mais alto"
    assert linhas["fonte"] == "ANFIR_2026"
    trailer = next(item for item in linhas["linhas"] if item["codigo"] == "trailer")
    diesel = next(item for item in linhas["linhas"] if item["codigo"] == "diesel_truck")
    direct = next(item for item in linhas["linhas"] if item["codigo"] == "direct_drive")
    assert trailer["mensal"][0] == 2
    assert diesel["mensal"][1] == 3
    assert direct["mensal"][2] == 1
    assert sum(trailer["mensal"]) == 2


def test_status_anfir_carrier_e_invalidos_nao_viram_perda():
    assert insights_router._eh_perda_anfir_2026({"ano": 2026, "status": "Carrier"}) is False
    assert insights_router._eh_perda_anfir_2026({"ano": 2026, "status": "UsadoCarrier"}) is False
    assert insights_router._eh_perda_anfir_2026({"ano": 2026, "status": "Nãoédessaregião"}) is False
    assert insights_router._eh_perda_anfir_2026({"ano": 2026, "status": "Nãoébaúfrigorífico"}) is False
    assert insights_router._eh_perda_anfir_2026({"ano": 2026, "status": ""}) is False


def test_status_anfir_concorrentes_e_sem_contato_sao_perda_comercial():
    for status in ("Nacional", "TK", "tk", "UsadoConcorrente", "Semcontato", "PERDIDO"):
        assert insights_router._eh_perda_anfir_2026({"ano": 2026, "status": status}) is True


def test_mes_registro_aceita_mes_numerico_textual_e_data_iso():
    assert insights_router._mes_registro({"mes": 3}) == 3
    assert insights_router._mes_registro({"mes": "setembro"}) == 9
    assert insights_router._mes_registro({"data": "2026-11-15"}) == 11
