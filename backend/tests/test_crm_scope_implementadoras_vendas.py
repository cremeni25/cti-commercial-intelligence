from types import SimpleNamespace

from routers import crm_scope_implementadoras_router as implementadoras
from routers import crm_scope_vendas_router as vendas


def usuario(tipo="REPRES_REGIAO_01", user_id="u1", acesso_total=False):
    return SimpleNamespace(
        id=user_id,
        nome="Usuário Teste",
        tipo_usuario=tipo,
        permissoes={"acesso_total": acesso_total},
    )


def test_implementadoras_usa_anfir_ja_filtrado_pelo_usuario(monkeypatch):
    recebido = {}

    def fake_anfir(user, contexto, periodo, uf, ddd, inicio, fim):
        recebido["usuario"] = user.id
        return ([{"implementadora": "IMP A", "cliente": "CLI A", "ddd": "012"}], None, None)

    monkeypatch.setattr(implementadoras, "_anfir_do_usuario", fake_anfir)
    monkeypatch.setattr(
        implementadoras,
        "consolidar_implementadoras",
        lambda registros: [{"nome": "IMP A", "quantidade_registros": len(registros)}],
    )
    monkeypatch.setattr(implementadoras, "_metadata_escopo", lambda user: {"usuario": user.nome})

    retorno = implementadoras.listar_implementadoras_seguras(usuario=usuario())
    assert recebido["usuario"] == "u1"
    assert retorno["itens"] == [{"nome": "IMP A", "quantidade_registros": 1}]


def test_venda_regional_nao_herda_pedido_de_outro_usuario(monkeypatch):
    user = usuario()
    monkeypatch.setattr(vendas, "_visao_consolidada", lambda _: False)
    monkeypatch.setattr(vendas, "_usa_escopo_proprio", lambda _: True)
    monkeypatch.setattr(vendas, "obter_oportunidade", lambda _id: {"responsavel_id": "u2"})

    def pedido_negado(_pedido_id, _usuario):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="fora do escopo")

    monkeypatch.setattr(vendas, "_pedido_autorizado", pedido_negado)
    assert vendas._venda_autorizada({"oportunidade_id": "opp-2", "pedido_id": "ped-2"}, user) is False


def test_venda_regional_aceita_oportunidade_propria(monkeypatch):
    user = usuario()
    monkeypatch.setattr(vendas, "_visao_consolidada", lambda _: False)
    monkeypatch.setattr(vendas, "_usa_escopo_proprio", lambda _: True)
    monkeypatch.setattr(vendas, "obter_oportunidade", lambda _id: {"responsavel_id": "u1"})
    assert vendas._venda_autorizada({"oportunidade_id": "opp-1"}, user) is True


def test_diretoria_consolidada_ve_venda(monkeypatch):
    user = usuario(tipo="DIRETOR_VIENA_SP", acesso_total=True)
    monkeypatch.setattr(vendas, "_visao_consolidada", lambda _: True)
    assert vendas._venda_autorizada({"id": "v1"}, user) is True
