from pathlib import Path

from services import commercial_client_scope as scope

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


def test_anfir_realizado_preserva_autoria_da_fonte_e_nao_usa_ddd(monkeypatch):
    fonte = SCOPE.read_text(encoding="utf-8")
    assert "resolver_ddd_registro" not in fonte
    assert "_usuarios_territoriais" not in fonte

    monkeypatch.setattr(scope, "_perfil_usuario", lambda usuario_id: {
        "id": usuario_id,
        "nome": "Monica Almeida" if usuario_id == "monica-id" else "Nathan Beljato",
    })

    sem_autor = {"ano": 2026, "cliente": "Cliente A", "ddd": "011"}
    autor_monica = {"ano": 2026, "cliente": "Cliente A", "ddd": "011", "responsavel": "MÔNICA"}
    autor_nathan = {"ano": 2026, "cliente": "Cliente A", "ddd": "011", "responsavel": "NATHAN"}

    assert scope.filtrar_anfir_por_responsavel_comercial([sem_autor], "monica-id", "Monica Almeida") == []
    assert scope.filtrar_anfir_por_responsavel_comercial([sem_autor], "nathan-id", "Nathan Beljato") == []
    assert scope.filtrar_anfir_por_responsavel_comercial([autor_monica], "monica-id", "Monica Almeida") == [autor_monica]
    assert scope.filtrar_anfir_por_responsavel_comercial([autor_monica], "nathan-id", "Nathan Beljato") == []
    assert scope.filtrar_anfir_por_responsavel_comercial([autor_nathan], "nathan-id", "Nathan Beljato") == [autor_nathan]


def test_crm_e_historico_priorizam_autoria_da_fonte_antes_da_carteira_atual():
    fonte = SCOPE.read_text(encoding="utf-8")
    bloco = fonte.split("def filtrar_carteira_exata_responsavel", 1)[1]
    pos_id_fonte = bloco.index("responsavel_id_fonte = _responsavel_id_registro")
    pos_nome_fonte = bloco.index("responsavel_fonte = _fold(_responsavel_registro")
    pos_cliente = bloco.index("cliente = _cliente_reconciliado")
    assert pos_id_fonte < pos_cliente
    assert pos_nome_fonte < pos_cliente
