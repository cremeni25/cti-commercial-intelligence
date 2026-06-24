import pandas as pd
from io import BytesIO


def processar_planilha_viena(contents):

    abas = pd.read_excel(
        BytesIO(contents),
        sheet_name=None
    )

    registros = []

    for nome_aba, df in abas.items():

        if "VIENA" not in nome_aba.upper():
            continue

        df = df.fillna("")

        for _, row in df.iterrows():

            registros.append({

                "data_venda":
                    str(row.get("DATA", "")),

                "responsavel":
                    str(row.get("RESPONSAVEL", "")),

                "regiao":
                    str(row.get("REGIAO", "")),

                "estado":
                    str(row.get("ESTADO", "")),

                "ddd":
                    str(row.get("DDD", "")),

                "cidade":
                    str(row.get("MUNICIPIO", "")),

                "sub_regiao":
                    str(row.get("SUB-REGIAO", "")),

                "cnpj":
                    str(row.get("CNPJ_FATURADO", "")),

                "fabricante_caminhao":
                    str(row.get("FABRICANTE CAMINHAO", "")),

                "modelo_caminhao":
                    str(row.get("MODELO CAMINHAO", "")),

                "eixo":
                    str(row.get("EIXO", "")),

                "tipo_veiculo":
                    str(row.get("TIPO_VEICULO", "")),

                "chassi":
                    str(row.get("CHASSI", "")),

                "placa":
                    str(row.get("PLACA", "")),

                "implementador":
                    str(row.get("IMPLEMENTADORA", "")),

                "cliente":
                    str(row.get("NOME_PROPRIETARIO", "")),

                "status":
                    str(row.get("STATUS", "")),

                "motivo":
                    str(row.get("MOTIVO", "")),

                "ocorrencia":
                    str(row.get("OCORRENCIA", "")),

                "fabricante_equipamento":
                    str(row.get(
                        "FABRICANTE EQUIPAMENTO",
                        ""
                    )),

                "linha":
                    str(row.get(
                        "LINHA DE PRODUTO",
                        ""
                    )),

                "modelo":
                    str(row.get(
                        "MODELO DE PRODUTO",
                        ""
                    )),

                "valor":
                    float(
                        row.get("VALOR", 0)
                        or 0
                    ),

                "origem_arquivo":
                    nome_aba
            })

    return registros