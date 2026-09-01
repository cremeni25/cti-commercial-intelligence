from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = (ROOT / "backend" / "routers" / "crm_atividades_governanca_router.py").read_text(encoding="utf-8")
FRONTEND = (ROOT / "frontend" / "src" / "app" / "crm-app" / "atividades" / "page.tsx").read_text(encoding="utf-8")


def test_backend_enriquece_atividade_com_responsavel_sem_alterar_fato_original():
    assert 'def _nomes_usuarios(' in BACKEND
    assert 'supabase.table("cti_users").select("id,nome,email")' in BACKEND
    assert 'registro["responsavel_id"] = usuario_id' in BACKEND
    assert 'registro["responsavel_nome"] = responsaveis.get(usuario_id, "")' in BACKEND
    assert 'registro["cliente_nome"] = nomes.get(cliente_id, "") or parceiro' in BACKEND


def test_central_exibe_responsavel_e_followup_acionavel_em_concluidas():
    assert 'responsavelNome:texto(i.responsavel_nome||i.usuario_nome||i.vendedor_nome)' in FRONTEND
    assert '{t.responsible}: {a.responsavelNome||t.responsibleUnknown}' in FRONTEND
    assert 'function followUpHref(a:Atividade)' in FRONTEND
    assert 'new URLSearchParams({tipo:"FOLLOW_UP"})' in FRONTEND
    assert 'if(a.clienteId)q.set("cliente",a.clienteId)' in FRONTEND
    assert 'if(a.oportunidadeId)q.set("oportunidade",a.oportunidadeId)' in FRONTEND
    assert 'finalizada&&<Link href={followUpHref(a)}' in FRONTEND
    assert 'Criar follow-up' in FRONTEND
