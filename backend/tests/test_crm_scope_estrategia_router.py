from types import SimpleNamespace

from routers import crm_scope_estrategia_router as modulo


def usuario(tipo="REPRES_REGIAO_01", identificador="user-1", nome="USUARIO TESTE", acesso_total=False):
    return SimpleNamespace(
        id=identificador,
        nome=nome,
        tipo_usuario=tipo,
        permissoes={"acesso_total": acesso_total},
    )


def test_crm_regional_filtra_por_responsavel(monkeypatch):
    monkeypatch.setattr(modulo, "carregar_oportunidades_enriquecidas", lambda: [
        {"id": "opp-1", "responsavel_id": "user-1"},
        {"id": "opp-2", "responsavel_id": "user-2"},
    ])
    assert [item["id"] for item in modulo._crm_do_usuario(usuario())] == ["opp-1"]


def test_usuario_com_acesso_total_recebe_crm_consolidado(monkeypatch):
    dados = [{"id": "opp-1"}, {"id": "opp-2"}]
    monkeypatch.setattr(modulo, "carregar_oportunidades_enriquecidas", lambda: dados)
    retorno = modulo._crm_do_usuario(usuario("DIRETOR_VIENA_SP", "dir-1", "DIRETOR TESTE", True))
    assert retorno == dados


def test_historico_regional_usa_representante_atual(monkeypatch):
    monkeypatch.setattr(modulo, "carregar_historico_comercial", lambda: (
        {"id": "h1", "representante_atual": "USUARIO", "data": "2026-01-01"},
        {"id": "h2", "representante_atual": "OUTRO", "data": "2026-01-01"},
    ))
    retorno = modulo._hist_do_usuario(usuario(nome="USUARIO TESTE"), None, None)
    assert [item["id"] for item in retorno] == ["h1"]


def test_anfir_regional_respeita_cadastro_de_ddds_e_codigo_regional(monkeypatch):
    monkeypatch.setattr(
        modulo,
        "_perfil_regional",
        lambda _: {"nome": "USUARIO TESTE", "ddds": ["011", "012"], "codigo_regional": "REGIAO 01"},
    )
    monkeypatch.setattr(modulo.estrategia, "_anfir", lambda *args, **kwargs: ([
        {"id": "a1", "ddd": "011"},
        {"id": "a1-regiao", "ddd": "011", "sub_regiao": "REGIAO 01"},
        {"id": "a1-outra", "ddd": "011", "sub_regiao": "REGIAO 02"},
        {"id": "a2", "ddd": "012"},
        {"id": "a3", "ddd": "013"},
    ], None, None))
    retorno, _, _ = modulo._anfir_do_usuario(usuario(), "brasil", "TODO_HISTORICO", None, None, None, None)
    assert [item["id"] for item in retorno] == ["a1-regiao", "a2"]


def test_anfir_novo_usuario_sem_ddd_cadastrado_nao_recebe_consolidado(monkeypatch):
    monkeypatch.setattr(
        modulo,
        "_perfil_regional",
        lambda _: {"nome": "NOVO USUARIO", "ddds": [], "codigo_regional": ""},
    )
    monkeypatch.setattr(modulo.estrategia, "_anfir", lambda *args, **kwargs: ([{"id": "a1", "ddd": "011"}], None, None))
    retorno, _, _ = modulo._anfir_do_usuario(usuario(tipo="USUARIO_CTI", nome="NOVO USUARIO"), "brasil", "TODO_HISTORICO", None, None, None, None)
    assert retorno == []


def test_anfir_bloqueia_ddd_fora_do_permitido(monkeypatch):
    monkeypatch.setattr(
        modulo,
        "_perfil_regional",
        lambda _: {"nome": "USUARIO TESTE", "ddds": ["011", "012"], "codigo_regional": "REGIAO 01"},
    )
    monkeypatch.setattr(modulo.estrategia, "_anfir", lambda *args, **kwargs: ([{"id": "a3", "ddd": "013"}], None, None))
    retorno, _, _ = modulo._anfir_do_usuario(usuario(), "brasil", "TODO_HISTORICO", None, "013", None, None)
    assert retorno == []
