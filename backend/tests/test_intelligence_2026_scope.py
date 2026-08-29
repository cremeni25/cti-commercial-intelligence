from datetime import date

from routers.analytics_router import _datas
from services.commercial_intelligence import consolidar_inteligencia, opcoes_filtros
from services.operational_filters import data_registro, filtrar_registros


def _registro(ano, mes, linha, status, motivo="", ocorrencia="", cliente="CLIENTE"):
    return {
        "ano": ano,
        "ano_referencia": ano,
        "mes": mes,
        "linha": linha,
        "status": status,
        "motivo": motivo,
        "ocorrencia": ocorrencia,
        "cliente": cliente,
        "origem_base": "VIENA_SP",
        "autorizado": "VIENA",
        "estado": "SP",
        "cidade": "SAO PAULO",
    }


def test_ano_atual_comeca_em_janeiro_do_ano_corrente():
    inicio, fim = _datas("ANO_ATUAL", None, None)
    assert inicio == date(date.today().year, 1, 1)
    assert fim == date.today()


def test_competencia_anfir_prevalece_sobre_data_venda_conflitante():
    registro = _registro(2026, 7, "DIRECT DRIVE", "TK", cliente="LEGADO-2025")
    registro.update({
        "ano_referencia": 2025,
        "aba_origem": "Viena SP 2025",
        "data_venda": "2026-01-01",
    })

    assert data_registro(registro) == date(2025, 7, 1)
    assert filtrar_registros(
        [registro],
        contexto="viena-sp",
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    ) == []


def test_motor_e_opcoes_excluem_legado_2025_com_data_venda_2026():
    legado = _registro(2026, 7, "DIRECT DRIVE", "TK", ocorrencia="OBSERVAÇÃO: preço antigo", cliente="LEGADO-2025")
    legado.update({
        "ano_referencia": 2025,
        "aba_origem": "Viena SP 2025",
        "data_venda": "2026-01-01",
    })
    atual = _registro(2026, 3, "DIRECT DRIVE", "TK", ocorrencia="OBSERVAÇÃO: preço atual", cliente="ATUAL-2026")
    atual["data_venda"] = "2026-03-15"
    filtros = {
        "inicio": date(2026, 1, 1), "fim": date(2026, 12, 31), "segmento": "DD",
        "regiao": None, "uf": None, "dealer": None, "implementadora": None,
        "cliente": None, "linha": None, "familia": None, "produto": None,
    }

    resultado = consolidar_inteligencia([legado, atual], contexto="viena-sp", segmento="DD", filtros=filtros, comparacao=None)
    assert resultado["kpis"]["volume"] == 1
    assert resultado["registros"][0]["cliente"] == "ATUAL-2026"
    assert resultado["registros"][0]["data_venda"] == "2026-03-01"

    opcoes = opcoes_filtros([legado, atual], filtros)
    clientes = {item["valor"] for item in opcoes["cliente"]}
    assert clientes == {"ATUAL-2026"}


def test_inteligencia_2026_exclui_historico_e_respeita_segmento_e_observacao():
    registros = [
        _registro(2025, 7, "DIRECT DRIVE", "TK", ocorrencia="OBSERVAÇÃO: perda antiga por preço", cliente="ANTIGO"),
        _registro(2026, 1, "TRAILER", "CARRIER", ocorrencia="OBSERVAÇÃO: relacionamento preservado", cliente="TR-2026"),
        _registro(2026, 2, "DIESEL TRUCK", "NACIONAL", motivo="Não participamos da proposta", ocorrencia="OBSERVAÇÃO: implementadora fabrica o equipamento", cliente="DT-2026"),
        _registro(2026, 3, "DIRECT DRIVE", "TK", motivo="Preço Carrier mais alto", ocorrencia="OBSERVAÇÃO: Thermo King com manutenção e preço", cliente="DD-2026"),
    ]
    filtros = {
        "inicio": date(2026, 1, 1),
        "fim": date(2026, 12, 31),
        "segmento": "DD",
        "regiao": None,
        "uf": None,
        "dealer": None,
        "implementadora": None,
        "cliente": None,
        "linha": None,
        "familia": None,
        "produto": None,
    }

    resultado = consolidar_inteligencia(registros, contexto="viena-sp", segmento="DD", filtros=filtros, comparacao=None)
    mercado = resultado["inteligencia_mercado"]

    assert mercado["mercado"]["volume"] == 1
    assert resultado["kpis"]["volume"] == 1
    assert mercado["competitividade"]["carrier_observado"]["quantidade"] == 0
    assert mercado["cobertura_comercial"]["nao_participamos_proposta"] == 0
    temas = {item["tema"] for item in mercado["inteligencia_observacoes"]["temas"]}
    assert "CONCORRENTE_TK" in temas
    assert "PRECO_VALOR" in temas
    assert "IMPLEMENTADORA_INTEGRADA" not in temas
    assert all("ANTIGO" != item["cliente"] for item in mercado["prioridades_recuperacao"])


def test_cada_segmento_e_subconjunto_do_mesmo_periodo_2026():
    registros = [
        _registro(2025, 1, "TRAILER", "CARRIER", cliente="TR-2025"),
        _registro(2026, 1, "TRAILER", "CARRIER", cliente="TR-2026"),
        _registro(2026, 2, "DIESEL TRUCK", "NACIONAL", cliente="DT-2026"),
        _registro(2026, 3, "DIRECT DRIVE", "TK", cliente="DD-2026"),
    ]
    base_filtros = {
        "inicio": date(2026, 1, 1),
        "fim": date(2026, 12, 31),
        "regiao": None,
        "uf": None,
        "dealer": None,
        "implementadora": None,
        "cliente": None,
        "linha": None,
        "familia": None,
        "produto": None,
    }
    volumes = {}
    for segmento in ("GERAL", "TR", "DT", "DD"):
        filtros = {**base_filtros, "segmento": segmento}
        resultado = consolidar_inteligencia(registros, contexto="viena-sp", segmento=segmento, filtros=filtros, comparacao=None)
        volumes[segmento] = resultado["inteligencia_mercado"]["mercado"]["volume"]

    assert volumes == {"GERAL": 3, "TR": 1, "DT": 1, "DD": 1}
    assert sum(volumes[codigo] for codigo in ("TR", "DT", "DD")) == volumes["GERAL"]


def test_segmentos_auxiliares_respeitam_periodo_sem_alterar_demais_blocos():
    registros = [
        _registro(2025, 1, "TRAILER", "CARRIER", ocorrencia="OBSERVAÇÃO: histórico antigo", cliente="TR-2025"),
        _registro(2026, 1, "TRAILER", "CARRIER", ocorrencia="OBSERVAÇÃO: relacionamento atual", cliente="TR-2026"),
        _registro(2026, 2, "DIESEL TRUCK", "NACIONAL", motivo="Não participamos da proposta", ocorrencia="OBSERVAÇÃO: implementadora fabrica o equipamento", cliente="DT-2026"),
        _registro(2026, 3, "DIRECT DRIVE", "TK", motivo="Preço Carrier mais alto", ocorrencia="OBSERVAÇÃO: Thermo King com manutenção e preço", cliente="DD-2026"),
    ]
    filtros = {
        "inicio": date(2026, 1, 1),
        "fim": date(2026, 12, 31),
        "segmento": "GERAL",
        "regiao": None,
        "uf": None,
        "dealer": None,
        "implementadora": None,
        "cliente": None,
        "linha": None,
        "familia": None,
        "produto": None,
    }

    resultado = consolidar_inteligencia(registros, contexto="viena-sp", segmento="GERAL", filtros=filtros, comparacao=None)
    mercado = resultado["inteligencia_mercado"]

    assert resultado["segmentos"] == {"TR": 1, "DT": 1, "DD": 1, "UNKNOWN": 0}
    assert resultado["kpis"]["volume"] == 3
    assert mercado["mercado"]["volume"] == 3
    assert mercado["competitividade"]["carrier_observado"]["quantidade"] == 1
    assert mercado["cobertura_comercial"]["nao_participamos_proposta"] == 1

    motivos = {item["motivo"]: item["quantidade"] for item in mercado["motivos_originais"]}
    assert motivos["Não participamos da proposta"] == 1
    assert motivos["Preço Carrier mais alto"] == 1

    temas = {item["tema"] for item in mercado["inteligencia_observacoes"]["temas"]}
    assert "CONCORRENTE_TK" in temas
    assert "PRECO_VALOR" in temas
    assert "IMPLEMENTADORA_INTEGRADA" in temas
    assert all("TR-2025" != item["cliente"] for item in mercado["prioridades_recuperacao"])
