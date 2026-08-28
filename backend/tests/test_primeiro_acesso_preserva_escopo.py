from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "primeiro_acesso_scope_router.py"
MAIN = ROOT / "backend" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "app" / "primeiro-acesso" / "page.tsx"


def test_primeiro_acesso_nao_grava_territorio_ou_ddds():
    codigo = ROUTER.read_text(encoding="utf-8")
    trecho = codigo.split("def concluir_primeiro_acesso_seguro", 1)[1]
    atualizacao = trecho.split("resposta =", 1)[0]

    assert '"territorio"' not in atualizacao
    assert '"ddds"' not in atualizacao
    assert '"tipo_usuario"' not in atualizacao
    assert "NÃO atualizar territorio, ddds, tipo_usuario ou permissões" in atualizacao


def test_router_seguro_tem_precedencia_sobre_governanca_legada():
    codigo = MAIN.read_text(encoding="utf-8")
    seguro = codigo.index("app.include_router(primeiro_acesso_scope_router)")
    legado = codigo.index("app.include_router(cti_api_router)")
    assert seguro < legado


def test_frontend_mostra_escopo_sem_campos_editaveis():
    codigo = FRONTEND.read_text(encoding="utf-8")
    assert "DDDs autorizados:" in codigo
    assert "Território autorizado:" in codigo
    assert 'label="Território"' not in codigo
    assert 'label="DDDs autorizados"' not in codigo
