from pathlib import Path

from routers.negociacoes_router import _registro_operacional, _titulo_oportunidade


ROUTER = Path(__file__).resolve().parents[1] / "routers" / "negociacoes_router.py"


def test_titulo_generico_usa_tipo_da_oportunidade_sem_trocar_titulo_legitimo():
    assert _titulo_oportunidade({
        "titulo": "Proposta Comercial",
        "descricao": "TIPO DA OPORTUNIDADE: Cotação / tomada de preços\nEquipamento: CITIMAX 400",
    }) == "Cotação / tomada de preços"
    assert _titulo_oportunidade({
        "titulo": "Tomada de Preços",
        "descricao": "TIPO DA OPORTUNIDADE: Cotação",
    }) == "Tomada de Preços"


def test_registro_operacional_exclui_testes_e_arquivados_sem_apagar_historico():
    assert _registro_operacional({"registro_teste": False, "arquivado_em": None}) is True
    assert _registro_operacional({"registro_teste": True, "arquivado_em": None}) is False
    assert _registro_operacional({"registro_teste": False, "arquivado_em": "2026-08-27T10:00:00Z"}) is False


def test_timeline_nao_consulta_fontes_inexistentes_nem_pedido_por_oportunidade_id():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "cti_oportunidade_historico" not in fonte
    assert '_consultar_oportunidade("cti_pedidos"' not in fonte
    assert 'in_("proposta_id"' in fonte
    assert 'in_("proposta_aceita_id"' in fonte
    assert 'in_("item_oportunidade_id"' in fonte
    assert '"cliente_nome": _nome_cliente' in fonte
