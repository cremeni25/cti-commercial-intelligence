from pathlib import Path


ARQUIVO = Path(__file__).resolve().parents[1] / "routers" / "crm_atividades_governanca_router.py"


def _fonte() -> str:
    return ARQUIVO.read_text(encoding="utf-8")


def test_arquivamento_escreve_na_tabela_fisica_e_nao_na_view_operacional():
    fonte = _fonte()
    assert 'TABELA_ATIVIDADES = "cti_atividades_registros"' in fonte
    assert 'VIEW_ATIVIDADES_ATIVAS = "cti_atividades"' in fonte
    trecho = fonte.split("def arquivar_atividade", 1)[1].split("@router.get(\"/dashboard\")", 1)[0]
    assert "supabase.table(TABELA_ATIVIDADES)" in trecho
    assert "supabase.table(VIEW_ATIVIDADES_ATIVAS).update" not in trecho


def test_listagem_de_arquivadas_le_a_tabela_fisica():
    fonte = _fonte()
    trecho = fonte.split("def listar_atividades_arquivadas", 1)[1].split("@router.put", 1)[0]
    assert "supabase.table(TABELA_ATIVIDADES)" in trecho
    assert '.not_.is_("arquivado_em", "null")' in trecho


def test_dashboard_conta_apenas_a_view_operacional():
    fonte = _fonte()
    trecho = fonte.split("def dashboard_crm_operacional", 1)[1]
    assert '"atividades": contar(VIEW_ATIVIDADES_ATIVAS)' in trecho
