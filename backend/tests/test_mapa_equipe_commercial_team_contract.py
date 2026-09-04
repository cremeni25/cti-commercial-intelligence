from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "crm_scope_mapa_equipe_router.py"
SCOPE = ROOT / "backend" / "services" / "commercial_client_scope.py"


def test_mapa_nao_agrega_perfis_corporativos_como_equipe_comercial():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "PERFIS_REGIONAIS |" not in fonte
    assert '"ADMIN_MASTER"' in fonte
    assert '"DIRETOR_VIENA_SP"' in fonte
    assert '"REPRES_REGIAO_01"' in fonte
    assert '"REPRES_REGIAO_02"' in fonte
    assert '"INDICADOR_VIENA_SP"' in fonte
    assert "ids_carteira = _ids_com_carteira_explicita()" in fonte
    assert 'or str(item.get("id") or "") in ids_carteira' in fonte


def test_macro_continua_sendo_uniao_das_mesmas_carteiras_individuais():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "anf_individual = _anfir_carteira(alvo, mercado_total)" in fonte
    assert "hist_individual = _historico_carteira(alvo, historico_base)" in fonte
    assert "crm_individual = _crm_carteira(alvo, crm_base)" in fonte
    assert "_deduplicar(anf_todos)" in fonte
    assert '"soma_mercado_individual"' in fonte
    assert '"sobreposicoes_entre_carteiras"' in fonte
    assert '"mercado_real_sem_carteira"' in fonte


def test_anfir_nao_retroage_responsabilidade_atual_do_cliente():
    fonte = SCOPE.read_text(encoding="utf-8")
    assert "_eh_anfir_realizado" in fonte
    assert "_anfir_pertence_ao_responsavel" in fonte
    assert "resolver_ddd_registro" in fonte
    assert 'ALIASES_RESPONSAVEL_ATUAL = {"CARLA": "MONICA"}' in fonte
    assert "DDD exclusivo" in fonte
    assert "sub_regiao = codigo_regional" in fonte
    bloco = fonte.split("if _eh_anfir_realizado(registro):", 1)[1].split("cliente = _cliente_reconciliado", 1)[0]
    assert "_cliente_reconciliado" not in bloco
