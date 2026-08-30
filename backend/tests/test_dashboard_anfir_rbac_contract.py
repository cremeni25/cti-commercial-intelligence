from pathlib import Path

from core.admin_auth import UsuarioAutenticado
from routers.crm_scope_estrategia_router import _registro_anfir_no_escopo


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "routers" / "anfir_workbook_router.py"
LAYOUT = ROOT / "frontend" / "src" / "app" / "layout.tsx"
BRIDGE = ROOT / "frontend" / "src" / "components" / "security" / "AuthenticatedAnfirFetchBridge.tsx"
ESTRATEGIA = ROOT / "backend" / "routers" / "crm_scope_estrategia_router.py"


def _usuario(tipo: str = "USUARIO_CTI", nome: str = "USUARIO TESTE") -> UsuarioAutenticado:
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


def test_escopo_anfir_e_orientado_ao_cadastro_e_nao_ao_nome_do_usuario():
    source = ESTRATEGIA.read_text(encoding="utf-8")
    assert 'supabase.table("cti_users")' in source
    assert '.select("nome,ddds,codigo_regional")' in source
    assert "permitidos = set(perfil[\"ddds\"])" in source
    assert "codigo_regional" in source
    assert "ddd_item = _ddd_workbook(item)" in source
    assert 'DDDS_COMPARTILHADOS = {"011"}' in source
    assert "RESPONSAVEIS_011_POR_PERFIL" not in source
    assert "SUBREGIAO_011_POR_PERFIL" not in source


def test_usuario_com_subdivisao_recebe_sua_regiao_no_ddd_compartilhado():
    usuario = _usuario(nome="NOVA REPRESENTANTE")
    perfil = {"nome": "NOVA REPRESENTANTE", "ddds": ["011", "012"], "codigo_regional": "REGIAO 03"}
    permitidos = {"011", "012"}
    assert _registro_anfir_no_escopo(_anfir(sub_regiao="REGIÃO 03"), usuario, permitidos, perfil)
    assert not _registro_anfir_no_escopo(_anfir(sub_regiao="REGIAO 02"), usuario, permitidos, perfil)


def test_continuidade_historica_ocorre_pela_regiao_sem_hardcode_de_pessoa():
    usuario = _usuario(nome="NOVA RESPONSAVEL")
    perfil = {"nome": "NOVA RESPONSAVEL", "ddds": ["011"], "codigo_regional": "REGIAO 01"}
    registro_antigo = _anfir(sub_regiao="REGIAO 01", responsavel="RESPONSAVEL ANTERIOR")
    assert _registro_anfir_no_escopo(registro_antigo, usuario, {"011"}, perfil)


def test_registro_sem_subregiao_no_ddd_compartilhado_exige_responsavel_atual():
    usuario = _usuario(nome="NOVA RESPONSAVEL")
    perfil = {"nome": "NOVA RESPONSAVEL", "ddds": ["011"], "codigo_regional": "REGIAO 01"}
    assert _registro_anfir_no_escopo(_anfir(responsavel="NOVA RESPONSAVEL"), usuario, {"011"}, perfil)
    assert not _registro_anfir_no_escopo(_anfir(responsavel="OUTRA PESSOA"), usuario, {"011"}, perfil)
    assert not _registro_anfir_no_escopo(_anfir(), usuario, {"011"}, perfil)


def test_ddd_nao_compartilhado_respeita_apenas_lista_autorizada():
    usuario = _usuario(nome="USUARIO REGIONAL")
    perfil = {"nome": "USUARIO REGIONAL", "ddds": ["012"], "codigo_regional": "REGIAO 99"}
    assert _registro_anfir_no_escopo(_anfir(ddd="012"), usuario, {"012"}, perfil)
    assert not _registro_anfir_no_escopo(_anfir(ddd="013"), usuario, {"012"}, perfil)


def test_usuario_sem_subdivisao_mantem_ddd_integral_quando_assim_cadastrado():
    usuario = _usuario(nome="GESTOR TERRITORIAL")
    perfil = {"nome": "GESTOR TERRITORIAL", "ddds": ["011"], "codigo_regional": ""}
    assert _registro_anfir_no_escopo(_anfir(sub_regiao="QUALQUER REGIAO"), usuario, {"011"}, perfil)


def test_ddd_auditado_por_municipio_prevalece_tambem_na_seguranca():
    usuario = _usuario(nome="USUARIO REGIONAL")
    perfil = {"nome": "USUARIO REGIONAL", "ddds": ["011"], "codigo_regional": "REGIAO 01"}
    registro = _anfir(ddd="015", cidade="SAO PAULO", sub_regiao="REGIAO 01")
    assert _registro_anfir_no_escopo(registro, usuario, {"011"}, perfil)


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
