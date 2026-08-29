from datetime import date

from services.commercial_intelligence import consolidar_inteligencia
from services.operational_filters import data_registro, filtrar_registros, resolver_ddd_registro


def _registro(**kwargs):
    base = {
        "ano": 2026,
        "mes": 1,
        "origem_base": "VIENA_SP",
        "autorizado": "VIENA",
        "estado": "SP",
        "cidade": "GUARULHOS",
        "linha": "Direct Drive",
        "cliente": "CLIENTE TESTE",
        "implementadora": "IBIPORA",
        "aba_origem": "Relatorio Performance 2026",
        "versao_parser": "3.1.0",
        "pipeline": "UPLOAD_ANFIR_OPERACIONAL",
        "ocorrencia": "REPRESENTAÇÃO: JOV",
        "created_at": "2026-08-29T12:00:00",
    }
    base.update(kwargs)
    return base


def test_competencia_anfir_usa_ano_mes_e_nao_data_upload():
    registro = _registro(mes=3)
    assert data_registro(registro) == date(2026, 3, 1)

    resultado = consolidar_inteligencia([registro], "viena-sp", "GERAL")
    assert resultado["serie_temporal"][0]["periodo"] == "2026-03"
    assert resultado["inteligencia_mercado"]["mercado"]["competencia_min"] == "2026-03-01"


def test_territorio_viena_deriva_ddd_por_municipio_e_exclui_019():
    guarulhos = _registro(cidade="GUARULHOS")
    louveira = _registro(cidade="LOUVEIRA", cliente="CLIENTE FORA")
    rio = _registro(estado="RJ", cidade="RIO DE JANEIRO", cliente="CLIENTE RJ")

    assert resolver_ddd_registro(guarulhos) == "011"
    assert resolver_ddd_registro(louveira) == "019"

    filtrados = filtrar_registros([guarulhos, louveira, rio], contexto="viena-sp")
    assert [r["cliente"] for r in filtrados] == ["CLIENTE TESTE"]
    assert filtrados[0]["ddd"] == "011"


def test_motor_publica_competitividade_causas_e_cobertura_sem_inventar_funil():
    registros = [
        _registro(cliente="A", status="Carrier", motivo=""),
        _registro(cliente="B", status="TK", motivo="Não participamos da proposta", ocorrencia="OBSERVAÇÃO: cliente já havia fechado com TK"),
        _registro(cliente="C", status="Nacional", motivo="Preço carrier mais alto", ocorrencia="OBSERVAÇÃO: fabricante nacional incluso no valor"),
        _registro(cliente="D", status="Semcontato", motivo="Falta de relacionamento", ocorrencia="OBSERVAÇÃO: necessário visitar o cliente"),
    ]

    resultado = consolidar_inteligencia(registros, "viena-sp", "GERAL")
    mercado = resultado["inteligencia_mercado"]
    distribuicao = {item["categoria"]: item["quantidade"] for item in mercado["competitividade"]["distribuicao"]}

    assert resultado["metricas_funil"]["disponiveis"] is False
    assert resultado["oportunidades_perdidas"]["quantidade"] is None
    assert resultado["metadata"]["motor_mercado"] == "ANFIR_INTELLIGENCE_002"
    assert mercado["mercado"]["volume"] == 4
    assert distribuicao["CARRIER"] == 1
    assert distribuicao["TK"] == 1
    assert distribuicao["NACIONAL"] == 1
    assert distribuicao["SEM_CONTATO"] == 1
    assert mercado["competitividade"]["carrier_observado"]["participacao_observada_percentual"] == 25.0
    assert mercado["cobertura_comercial"]["nao_participamos_proposta"] == 1
    assert mercado["cobertura_comercial"]["sem_contato"] == 1
    assert mercado["prioridades_recuperacao"][0]["cliente"] in {"B", "D"}


def test_comparacao_de_mercado_retorna_crescimento_real():
    registros = [
        _registro(mes=1, cliente="JAN-A", status="Carrier"),
        _registro(mes=1, cliente="JAN-B", status="TK"),
        _registro(mes=2, cliente="FEV-A", status="Carrier"),
        _registro(mes=2, cliente="FEV-B", status="TK"),
        _registro(mes=2, cliente="FEV-C", status="Nacional"),
    ]
    filtros = {"segmento": "GERAL", "inicio": date(2026, 2, 1), "fim": date(2026, 2, 28)}
    comparacao = {"segmento": "GERAL", "inicio": date(2026, 1, 1), "fim": date(2026, 1, 31)}

    resultado = consolidar_inteligencia(registros, "viena-sp", "GERAL", filtros, comparacao)
    variacao = resultado["inteligencia_mercado"]["mercado"]["comparacao"]
    assert variacao["atual"] == 3
    assert variacao["anterior"] == 2
    assert variacao["percentual"] == 50.0
    assert variacao["direcao"] == "alta"
