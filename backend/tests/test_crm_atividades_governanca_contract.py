from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = (ROOT / "routers" / "crm_atividades_governanca_router.py").read_text(encoding="utf-8")
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
FRONTEND = (ROOT.parent / "frontend" / "src" / "app" / "crm-app" / "atividades" / "page.tsx").read_text(encoding="utf-8")
CLIENTE = (ROOT.parent / "frontend" / "src" / "app" / "crm-app" / "clientes" / "[clienteId]" / "page.tsx").read_text(encoding="utf-8")


def test_leitura_operacional_exclui_arquivadas_e_resolve_cliente():
    assert '.is_("arquivado_em", "null")' in ROUTER
    assert 'registro["cliente_nome"]' in ROUTER
    assert 'supabase.table("clientes").select("id,nome")' in ROUTER


def test_governanca_vem_antes_do_router_crm_legado():
    governanca = MAIN.index("app.include_router(crm_atividades_governanca_router)")
    legado = MAIN.index("app.include_router(crm_router)")
    assert governanca < legado


def test_edicao_e_arquivamento_exigem_master_e_auditam():
    assert 'tipo_usuario") or "").upper() != "ADMIN_MASTER"' in ROUTER
    assert '"EDICAO_ADMIN_MASTER"' in ROUTER
    assert '"ARQUIVAMENTO_ADMIN_MASTER"' in ROUTER
    assert 'cti_atividades_auditoria' in ROUTER


def test_frontend_master_corrige_sem_criar_nova_atividade():
    assert "/administrar" in FRONTEND
    assert "/arquivar" in FRONTEND
    assert "Nenhuma nova atividade foi criada" in FRONTEND
    assert "Atividades arquivadas" not in FRONTEND or "Arquivadas" in FRONTEND


def test_dossie_nao_faz_fallback_do_codigo_para_uuid():
    assert "codigo: texto(cadastro?.codigo || cadastro?.codigo_cliente)," in CLIENTE
    assert "{cliente.codigo &&" in CLIENTE
