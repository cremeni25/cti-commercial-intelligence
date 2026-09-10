from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCA = (ROOT / "routers" / "crm_atividades_governanca_router.py").read_text(encoding="utf-8")
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_conclusao_operacional_grava_na_tabela_base():
    assert '@router.put("/atividades/{atividade_id}/concluir")' in GOVERNANCA
    assert 'supabase.table(TABELA_ATIVIDADES).update(payload)' in GOVERNANCA
    assert '"status": "CONCLUIDA"' in GOVERNANCA
    assert '"concluida_em": _now()' in GOVERNANCA


def test_governanca_continua_antes_do_router_crm_legado():
    assert MAIN.index("app.include_router(crm_atividades_governanca_router)") < MAIN.index("app.include_router(crm_router)")
