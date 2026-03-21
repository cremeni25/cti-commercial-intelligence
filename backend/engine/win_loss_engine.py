# engine/win_loss_engine.py

import pandas as pd

class WinLossEngine:

    def __init__(self, anf_ir_data, negociacoes_data):

        self.anfir = pd.DataFrame(anf_ir_data)
        self.neg = pd.DataFrame(negociacoes_data)

        # segurança
        if self.anfir.empty:
            self.anfir = pd.DataFrame(columns=["cliente_id", "estado", "linha", "segmento"])

        if self.neg.empty:
            self.neg = pd.DataFrame(columns=[
                "cliente_id", "produto", "status",
                "valor_estimado", "motivo_perda"
            ])

    # ------------------------------
    # NORMALIZAÇÃO
    # ------------------------------

    def normalizar(self):

        if not self.neg.empty:
            self.neg["status"] = self.neg["status"].astype(str).str.upper().str.strip()
            self.neg["produto"] = self.neg["produto"].astype(str).str.upper().str.strip()

    # ------------------------------
    # CRUZAMENTO POR CLIENTE_ID
    # ------------------------------

    def cruzar_dados(self):

        if self.neg.empty:
            return pd.DataFrame()

        merged = pd.merge(
            self.neg,
            self.anfir,
            on="cliente_id",
            how="left",
            suffixes=("_neg", "_anfir")
        )

        return merged

    # ------------------------------
    # WIN / LOSS
    # ------------------------------

    def calcular_win_loss(self):

        self.normalizar()
        base = self.cruzar_dados()

        if base.empty:
            return {
                "resumo": {
                    "total_negociacoes": 0,
                    "ganhos": 0,
                    "perdas": 0,
                    "taxa_conversao": 0
                },
                "detalhado": []
            }

        ganhos = base[base["status"] == "GANHO"]
        perdas = base[base["status"] == "PERDIDO"]

        total = len(base)
        total_ganhos = len(ganhos)
        total_perdas = len(perdas)

        taxa = (total_ganhos / total * 100) if total > 0 else 0

        return {
            "resumo": {
                "total_negociacoes": int(total),
                "ganhos": int(total_ganhos),
                "perdas": int(total_perdas),
                "taxa_conversao": round(taxa, 2)
            },
            "detalhado": base.fillna("").to_dict(orient="records")
        }

    # ------------------------------
    # INSIGHTS
    # ------------------------------

    def insights(self):

        self.normalizar()
        base = self.cruzar_dados()

        if base.empty:
            return []

        insights = []

        perdas = base[base["status"] == "PERDIDO"]

        for _, row in perdas.iterrows():

            insights.append({
                "cliente_id": row.get("cliente_id"),
                "produto": row.get("produto"),
                "estado": row.get("estado"),
                "segmento": row.get("segmento"),
                "valor_estimado": row.get("valor_estimado"),
                "motivo_perda": row.get("motivo_perda"),
                "alerta": "Perda — revisar estratégia comercial"
            })

        return insights
