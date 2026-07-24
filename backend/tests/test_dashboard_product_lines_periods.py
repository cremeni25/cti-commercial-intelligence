from datetime import date

from routers.analytics_router import _datas, _periodo_linhas


def test_periodos_predefinidos_retornam_janela():
    for periodo in ("ULTIMOS_30_DIAS", "ULTIMOS_90_DIAS", "MES_ATUAL", "TRIMESTRE_ATUAL", "ANO_ATUAL"):
        inicio, fim = _datas(periodo, None, None)
        assert isinstance(inicio, date)
        assert isinstance(fim, date)
        assert inicio <= fim


def test_personalizado_sem_datas_retorna_90_dias():
    periodo, inicio, fim, descricao = _periodo_linhas("PERSONALIZADO", None, None)
    assert periodo == "ULTIMOS_90_DIAS"
    assert inicio is None
    assert fim is None
    assert "90 dias" in descricao


def test_todo_historico_retorna_90_dias_para_relogios():
    periodo, inicio, fim, descricao = _periodo_linhas("TODO_HISTORICO", None, None)
    assert periodo == "ULTIMOS_90_DIAS"
    assert inicio is None
    assert fim is None
    assert "90 dias" in descricao
