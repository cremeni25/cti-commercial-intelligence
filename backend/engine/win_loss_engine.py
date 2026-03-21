import pandas as pd

class WinLossEngine:

    def __init__(self, anf ir_data, negociacoes_data):

        self.anfir = pd.DataFrame(anf ir_data)
        self.neg = pd.DataFrame(negociacoes_data)

    # --------------------------------------------------
    # NORMALIZAÇÃO
    # --------------------------------------------------

    def normalizar(self, df):

        if df.empty:
            return df

        for col in ["estado", "cidade", "segmento", "linha"]:

            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().str.strip()

        return df

    # --------------------------------------------------
    # CRUZAMENTO PRINCIPAL
    # --------------------------------------------------

    def cruzar(self):

        if self.anfir.empty or self.neg.empty:
            return {
                "status": "sem dados suficientes"
            }

        anf ir = self.normalizar(self.anfir.copy())
        neg = self.normalizar(self.neg.copy())

        resultado = []

        for _, venda in anf ir.iterrows():

            match = neg[
                (neg["estado"] == venda.get("estado")) &
                (neg["segmento"] == venda.get("segmento"))
            ]

            if match.empty:

                resultado.append({
                    "estado": venda.get("estado"),
                    "segmento": venda.get("segmento"),
                    "status": "PERDA",
                    "motivo": "sem negociação registrada"
                })

            else:

                for _, n in match.iterrows():

                    status = (n.get("status") or "").upper()

                    if "FECHADO" in status or "GANHO" in status:

                        resultado.append({
                            "estado": venda.get("estado"),
                            "segmento": venda.get("segmento"),
                            "status": "GANHO",
                            "motivo": "negociação convertida"
                        })

                    else:

                        resultado.append({
                            "estado": venda.get("estado"),
                            "segmento": venda.get("segmento"),
                            "status": "PERDA",
                            "motivo": "negociação não convertida"
                        })

        return resultado

    # --------------------------------------------------
    # RESUMO EXECUTIVO
    # --------------------------------------------------

    def resumo(self):

        dados = self.cruzar()

        if isinstance(dados, dict):
            return dados

        df = pd.DataFrame(dados)

        total = len(df)

        ganhos = len(df[df["status"] == "GANHO"])
        perdas = len(df[df["status"] == "PERDA"])

        taxa = (ganhos / total) * 100 if total > 0 else 0

        return {
            "total": total,
            "ganhos": ganhos,
            "perdas": perdas,
            "taxa_conversao": round(taxa, 2)
        }
