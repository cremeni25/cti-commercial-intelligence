from io import BytesIO

import pandas as pd

from parsers.viena_parser import processar_planilha_viena_com_relatorio


def _xlsx(abas):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nome, linhas in abas.items():
            pd.DataFrame(linhas).to_excel(writer, sheet_name=nome, index=False, header=False)
    return buffer.getvalue()


def test_parser_carrier_jov_isola_anfir_do_bloco_lateral_e_preserva_contexto():
    cabecalho = [
        "REPRESENTAÇÃO", None, "Mês", "REGIAO", "ESTADO", "MUNICIPIO",
        "CAMINHÃO", "MODELO", "FABRICANTE", "PRODUTO", "TIPO VEICULO",
        "CHASSI", "TOTAL", "SEGMENTO", "Cliente", "Rep", "STATUS",
        "MOTIVO CONCORRENTE", "OBSERVAÇÃO", "PLANO AÇÃO 1", "QUANDO?",
        "STATUS PLANO AÇÃO 1", None,
        "DATA VENDA", "CLIENTE", "QTD", "MODELO",
    ]
    linha = [
        "JOV", None, "Janeiro", "SUDESTE", "SP", "GUARULHOS",
        0, 0, "IBIPORA", "BAU FRIGORIFICO", "SEMIRREBOQUE",
        "9A9TESTE123", 1, "TRAILER", "CLIENTE ANFIR", "JOV", "TK",
        "Não participamos da proposta", "Cliente já havia decidido pelo concorrente",
        "Retomar contato", "Fevereiro", "Em andamento", None,
        "2025-01-21", "CLIENTE BLOCO LATERAL", 1, "X4 7500",
    ]

    registros, relatorio = processar_planilha_viena_com_relatorio(
        _xlsx({"Relatorio Performance 2026": [cabecalho, linha]}),
        "carrier-jov.xlsx",
    )

    assert len(registros) == 1
    registro = registros[0]
    assert registro["cliente"] == "CLIENTE ANFIR"
    assert registro["cliente"] != "CLIENTE BLOCO LATERAL"
    assert registro["ano"] == 2026
    assert registro["mes"] == 1
    assert registro["data_venda"] == ""
    assert registro["linha"] == "TRAILER"
    assert registro["status"] == "TK"
    assert registro["motivo"] == "Não participamos da proposta"
    assert registro["responsavel"] == ""
    assert registro["implementadora"]
    assert "REPRESENTAÇÃO: JOV" in registro["ocorrencia"]
    assert "OBSERVAÇÃO: Cliente já havia decidido pelo concorrente" in registro["ocorrencia"]
    assert "PLANO AÇÃO 1: Retomar contato" in registro["ocorrencia"]
    assert "QUANDO: Fevereiro" in registro["ocorrencia"]
    assert "STATUS PLANO AÇÃO 1: Em andamento" in registro["ocorrencia"]
    assert relatorio["bases_processadas"]["VIENA_SP"]["registros_validos"] == 1


def test_parser_carrier_jov_descarta_placeholders_qualitativos_sem_perder_registro():
    cabecalho = [
        "REPRESENTAÇÃO", "Mês", "REGIAO", "ESTADO", "MUNICIPIO", "FABRICANTE",
        "TIPO VEICULO", "CHASSI", "SEGMENTO", "Cliente", "Rep", "STATUS",
        "MOTIVO CONCORRENTE", "OBSERVAÇÃO", "PLANO AÇÃO 1", "QUANDO?", "STATUS PLANO AÇÃO 1",
    ]
    linha = [
        "JOV", "Março", "SUDESTE", "SP", "SAO PAULO", "FACCHINI",
        "3/4", "CHASSI002", "DIRECT DRIVE", "CLIENTE B", "JOV", "Nacional",
        80, 80, 80, 80, 80,
    ]

    registros, _ = processar_planilha_viena_com_relatorio(
        _xlsx({"Relatorio Performance 2026": [cabecalho, linha]}),
        "carrier-jov.xlsx",
    )

    assert len(registros) == 1
    assert registros[0]["mes"] == 3
    assert registros[0]["motivo"] == ""
    assert registros[0]["ocorrencia"] == "REPRESENTAÇÃO: JOV"


def test_parser_canonico_legado_permanece_funcional():
    cabecalho = ["DATA", "CLIENTE", "CHASSI", "LINHA DE PRODUTO", "STATUS"]
    linha = ["2026-07-15", "CLIENTE LEGADO", "CHASSI-LEGADO", "TRAILER", "Carrier"]

    registros, relatorio = processar_planilha_viena_com_relatorio(
        _xlsx({"VIENA SP 2026": [cabecalho, linha]}),
        "legado.xlsx",
    )

    assert len(registros) == 1
    assert registros[0]["cliente"] == "CLIENTE LEGADO"
    assert registros[0]["ano"] == 2026
    assert registros[0]["mes"] == 7
    assert registros[0]["linha"] == "TRAILER"
    assert relatorio["bases_processadas"]["VIENA_SP"]["registros_validos"] == 1
