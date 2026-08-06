from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def _ler(caminho: str) -> str:
    return (BASE / caminho).read_text(encoding="utf-8")


def test_backend_minimo_carrega_apenas_rota_experimental():
    codigo = _ler("main_ia_homologacao.py")
    assert "ia_comercial_agente_homologacao_router" in codigo
    assert "app.include_router(ia_agente_router)" in codigo
    for rota_operacional in (
        "crm_router",
        "propostas_pedidos_router",
        "governanca_usuarios_router",
        "modelos_proposta_storage_router",
    ):
        assert rota_operacional not in codigo


def test_memoria_escreve_somente_no_schema_isolado():
    codigo = _ler("services/ia_homologacao_memoria.py")
    assert 'SCHEMA = "ia_homologacao"' in codigo
    assert "supabase.schema(SCHEMA).table(nome)" in codigo
    assert 'table("cti_' not in codigo
    assert 'schema("public")' not in codigo


def test_agente_nao_expoe_ferramentas_operacionais_de_escrita():
    codigo = _ler("services/ia_comercial_agente_homologacao.py").lower()
    ferramentas_proibidas = (
        '"criar_',
        '"atualizar_',
        '"excluir_',
        '"deletar_',
        '"aprovar_',
        '"enviar_proposta',
    )
    for termo in ferramentas_proibidas:
        assert termo not in codigo


def test_migration_da_ia_preserva_schema_public():
    sql = _ler("migrations/homologacao/20260806_area_ia_homologacao.sql").lower()
    assert "create schema if not exists ia_homologacao" in sql
    assert "create table if not exists ia_homologacao." in sql
    assert "create table public." not in sql
    assert "alter table public." not in sql
    assert "drop table" not in sql
    assert "truncate" not in sql


def test_scripts_de_espelho_possuem_bloqueios_de_seguranca():
    exportacao = (BASE.parent / "scripts/espelho/exportar_estado_real.sh").read_text(encoding="utf-8")
    assert "xhrikmksydsyalxkkyot" in exportacao
    assert "origem e destino" in exportacao.lower()
    assert "schema public" in exportacao.lower()
    assert "sha256" in exportacao.lower() or "shasum" in exportacao.lower()
