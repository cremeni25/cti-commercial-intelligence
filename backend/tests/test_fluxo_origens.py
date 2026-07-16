from io import BytesIO

import pandas as pd

from parsers.viena_parser import processar_planilha_viena_com_relatorio
from services.base_analytics import (
    consolidar_dashboard,
    consolidar_historico,
    filtrar_registros,
)

CABECALHO = [
    "DATA",
    "RESPONSAVEL",
    "REGIAO",
    "ESTADO",
    "DDD",
    "MUNICIPIO",
    "SUB-REGIAO",
    "CNPJ_FATURADO",
    "FABRICANTE CAMINHAO",
    "MODELO CAMINHAO",
    "EIXO",
    "TIPO_VEICULO",
    "CHASSI",
    "PLACA",
    "IMPLEMENTADORA",
    "NOME_PROPRIETARIO",
    "STATUS",
    "MOTIVO",
    "OCORRENCIA",
    "FABRICANTE EQUIPAMENTO",
    "LINHA DE PRODUTO",
    "MODELO DE PRODUTO - CARRIER",
    "MODELO DE PRODUTO - CONCORRÊNCIA",
    "VALOR",
]


def linha(chassi, placa, cliente, valor, data=45292, estado="SP"):
    return [
        data,
        "Ana",
        "Sudeste",
        estado,
        "11",
        "São Paulo",
        "Capital",
        "12345678000199",
        "Volvo",
        "FH",
        "6x2",
        "TRUCK",
        chassi,
        placa,
        "RANDON",
        cliente,
        "APROVADO",
        "CARRIER",
        "OK",
        "CARRIER",
        "TRAILER",
        "XARIOS",
        "THERMO",
        valor,
    ]


def workbook():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([["lista"]]).to_excel(writer, sheet_name="Dados", index=False, header=False)
        pd.DataFrame(
            [
                CABECALHO,
                linha("CHASSI-1", "AAA1A11", "Cliente Brasil", 1000),
                linha("CHASSI-1", "AAA1A11", "Cliente Brasil Duplicado", 1000),
                linha("CHASSI-BR", "BBB1B11", "Cliente Brasil 2", 2000),
            ]
        ).to_excel(writer, sheet_name="Brasil", index=False, header=False)
        pd.DataFrame(
            [
                CABECALHO,
                linha("CHASSI-1", "AAA1A11", "Cliente Viena", 3000, data=45658),
                linha("CHASSI-1", "AAA1A11", "Cliente Viena Duplicado", 3000, data=45658),
                linha("CHASSI-VI", "CCC1C11", "Cliente Viena 2", 4000, data=45659),
            ]
        ).to_excel(writer, sheet_name="Viena SP 2025", index=False, header=False)
        pd.DataFrame(
            [
                CABECALHO,
                linha("CHASSI-1", "AAA1A11", "Cliente Viena 2026", 5000, data=46023),
            ]
        ).to_excel(writer, sheet_name="Viena SP 2026", index=False, header=False)
        pd.DataFrame([CABECALHO]).to_excel(writer, sheet_name="Viena SP 2024", index=False, header=False)
    return buffer.getvalue()


def test_origens_sao_independentes_e_deduplicadas():
    registros, relatorio = processar_planilha_viena_com_relatorio(workbook(), "teste.xlsx")

    brasil = filtrar_registros(registros, "BRASIL")
    viena = filtrar_registros(registros, "VIENA_SP", "VIENA")

    assert len(brasil) == 2
    assert len(viena) == 3
    assert any(r["chassi"] == "CHASSI-1" for r in brasil)
    assert any(r["chassi"] == "CHASSI-1" for r in viena)
    assert relatorio["bases_processadas"]["BRASIL"]["duplicados_ignorados"] == 1
    assert relatorio["bases_processadas"]["VIENA_SP"]["duplicados_ignorados"] == 1
    assert all(r["origem_base"] == "BRASIL" for r in brasil)
    assert all(r["origem_base"] == "VIENA_SP" for r in viena)
    assert all(r["autorizado"] == "VIENA" for r in viena)


def test_metricas_e_historico_respeitam_contexto():
    registros, _ = processar_planilha_viena_com_relatorio(workbook(), "teste.xlsx")
    brasil = filtrar_registros(registros, "BRASIL")
    viena = filtrar_registros(registros, "VIENA_SP", "VIENA")

    dash_brasil = consolidar_dashboard(brasil)
    dash_viena = consolidar_dashboard(viena)
    historico_viena = consolidar_historico(viena)

    assert dash_brasil["total_registros"] == 2
    assert dash_viena["total_registros"] == 3
    assert dash_brasil["faturamento_total"] == 3000
    assert dash_viena["faturamento_total"] == 12000
    assert historico_viena == [
        {"ano": "2025", "quantidade_registros": 2},
        {"ano": "2026", "quantidade_registros": 1},
    ]
