from types import SimpleNamespace

from routers import crm_scope_cliente_referencia_router as modulo


def usuario_regional():
    return SimpleNamespace(id="user-1", tipo_usuario="REPRES_REGIAO_01", permissoes={})


def dados(cliente_id="cliente-1", responsavel="user-2"):
    return modulo.ClienteOportunidadeCreate(
        cliente=modulo.legado.ClienteContexto(
            id=cliente_id,
            nome="Cliente informado no formulário",
            cidade="Cidade informada",
            estado="SP",
        ),
        oportunidade=modulo.legado.OportunidadeContexto(
            responsavel_id=responsavel,
            titulo="Cotação",
            valor_estimado=1000,
            probabilidade=50,
        ),
    )


def test_cliente_existente_e_apenas_referenciado(monkeypatch):
    existente = {"id": "cliente-1", "nome": "Cadastro mestre preservado", "cidade": "Cidade original"}
    monkeypatch.setattr(modulo, "_cliente_operacional_por_id", lambda _: existente)
    chamado = {"atualizacao": False}

    def nao_deve_atualizar(_):
        chamado["atualizacao"] = True
        raise AssertionError("cadastro existente não pode ser atualizado implicitamente")

    monkeypatch.setattr(modulo.legado, "_criar_ou_atualizar_cliente", nao_deve_atualizar)
    cliente, compat = modulo._resolver_cliente(dados())

    assert cliente == existente
    assert compat["mode"] == "referencia_existente"
    assert chamado["atualizacao"] is False


def test_cliente_novo_pode_ser_materializado(monkeypatch):
    monkeypatch.setattr(modulo, "_cliente_operacional_por_id", lambda _: None)
    novo = {"id": "cliente-novo", "nome": "Cliente Novo"}
    monkeypatch.setattr(modulo.legado, "_criar_ou_atualizar_cliente", lambda _: (novo, {"mode": "novo"}))

    cliente, compat = modulo._resolver_cliente(dados(cliente_id=""))

    assert cliente == novo
    assert compat["mode"] == "novo"


def test_criacao_regional_forca_responsavel_da_sessao(monkeypatch):
    monkeypatch.setattr(modulo, "_resolver_cliente", lambda _: ({"id": "cliente-1"}, {"mode": "referencia_existente"}))
    capturado = {}

    def criar(dados_recebidos, cliente, compat):
        capturado["responsavel"] = dados_recebidos.oportunidade.responsavel_id
        return {"cliente": cliente, "compatibilidade": compat}

    monkeypatch.setattr(modulo, "_criar_oportunidade", criar)
    modulo.criar_cliente_oportunidade_por_referencia(dados(), usuario_regional())

    assert capturado["responsavel"] == "user-1"
