from pathlib import Path

from core.admin_auth import UsuarioAutenticado
from routers.crm_scope_estrategia_router import _registro_anfir_no_escopo


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "routers" / "anfir_workbook_router.py"
LAYOUT = ROOT / "frontend" / "src" / "app" / "layout.tsx"
BRIDGE = ROOT / "frontend" / "src" / "components" / "security" / "AuthenticatedAnfirFetchBridge.tsx"
ESTRATEGIA = ROOT / "backend" / "routers" / "crm_scope_estrategia_router.py"


def _usuario(tipo: str, nome: str) -> UsuarioAutenticado:
    return UsuarioAutenticado(
        id=f"id-{tipo}",
        auth_id=f"auth-{tipo}",
        email=f"{tipo.lower()}@cti.local",
        nome=nome,
        tipo_usuario=tipo,
        permissoes={},
    )


def _anfir(ddd="011", sub_regiao="", responsavel="", cidade="", estado="SP"):
    return {
        "ddd": ddd,
        "sub_regiao": sub_regiao,
        "responsavel": responsavel,
        "cidade": cidade,
        "estado": estado,
    }


def test_workbook_anfir_exige_usuario_e_reutiliza_escopo_territorial():
    source = BACKEND.read_text(encoding="utf-8")
    assert "Depends(usuario_atual)" in source
    assert "_anfir_do_usuario" in source
    assert 'contexto="viena-sp"' in source
    assert 'periodo="PERSONALIZADO"' in source
    assert "_metadata_escopo(usuario)" in source


def test_escopo_regional_usa_ddds_cadastrados_e_semantica_auditada():
    source = ESTRATEGIA.read_text(encoding="utf-8")
    assert 'supabase.table("cti_users")' in source
    assert '.select("nome,ddds")' in source
    assert "permitidos = set(perfil[\"ddds\"])" in source
    assert "ddd_item = _ddd_workbook(item)" in source
    assert 'DDD_011_COMPARTILHADO = "011"' in source


def test_monica_recebe_regiao_01_e_continuidade_historica_da_carla_no_011():
    monica = _usuario("REPRES_REGIAO_01", "Monica Almeida")
    permitidos = {"011", "012"}
    assert _registro_anfir_no_escopo(_anfir(sub_regiao="REGIAO 01"), monica, permitidos)
    assert _registro_anfir_no_escopo(_anfir(responsavel="CARLA"), monica, permitidos)
    assert _registro_anfir_no_escopo(_anfir(responsavel="MÔNICA ALMEIDA"), monica, permitidos)
    assert not _registro_anfir_no_escopo(_anfir(sub_regiao="REGIAO 02", responsavel="MICHELE"), monica, permitidos)
    assert not _registro_anfir_no_escopo(_anfir(), monica, permitidos)


def test_monica_recebe_ddd_012_integral_e_michele_nao_recebe_012():
    monica = _usuario("REPRES_REGIAO_01", "Monica Almeida")
    michele = _usuario("REPRES_REGIAO_02", "Michele Santos")
    registro = _anfir(ddd="012", cidade="TAUBATE")
    assert _registro_anfir_no_escopo(registro, monica, {"011", "012"})
    assert not _registro_anfir_no_escopo(registro, michele, {"011", "013"})


def test_michele_recebe_regiao_02_e_nao_regiao_01_no_011():
    michele = _usuario("REPRES_REGIAO_02", "Michele Santos")
    permitidos = {"011", "013"}
    assert _registro_anfir_no_escopo(_anfir(sub_regiao="REGIÃO 02"), michele, permitidos)
    assert _registro_anfir_no_escopo(_anfir(responsavel="MICHELE SANTOS"), michele, permitidos)
    assert not _registro_anfir_no_escopo(_anfir(sub_regiao="REGIAO 01", responsavel="CARLA"), michele, permitidos)


def test_ddd_auditado_por_municipio_prevalece_tambem_na_seguranca():
    monica = _usuario("REPRES_REGIAO_01", "Monica Almeida")
    registro = _anfir(ddd="015", cidade="SAO PAULO", sub_regiao="REGIAO 01")
    assert _registro_anfir_no_escopo(registro, monica, {"011", "012"})


def test_equipamento_seguro_preserva_camadas_existentes():
    source = ESTRATEGIA.read_text(encoding="utf-8")
    assert '"realizado": estrategia._camada_anfir(anf)' in source
    assert '"historico_comercial": estrategia._camada_historico(historico)' in source
    assert '"em_curso": estrategia._camada_crm(crm)' in source


def test_frontend_autentica_as_leituras_existentes_sem_reescrever_dashboard():
    layout = LAYOUT.read_text(encoding="utf-8")
    bridge = BRIDGE.read_text(encoding="utf-8")
    assert "<AuthenticatedAnfirFetchBridge />" in layout
    assert 'ANFIR_WORKBOOK_PATH = "/api/cti/analytics/anfir-workbook-2026"' in bridge
    assert "supabase.auth.getSession()" in bridge
    assert 'headers.set("Authorization", `Bearer ${token}`)' in bridge
    assert "if (!url.includes(ANFIR_WORKBOOK_PATH))" in bridge


def test_correcao_nao_adiciona_escrita_na_base_anfir():
    for path in (BACKEND, ESTRATEGIA):
        source = path.read_text(encoding="utf-8")
        forbidden = ["insert(", "update(", "delete(", ".upsert(", ".insert(", ".update(", ".delete("]
        for token in forbidden:
            assert token not in source
