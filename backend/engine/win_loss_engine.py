# engine/win_loss_engine.py

import pandas as pd

class WinLossEngine:

    def __init__(self, anf_ir_data, negociacoes_data):

        # DataFrames
        self.anfir = pd.DataFrame(anf_ir_data)
        self.neg = pd.DataFrame(negociacoes_data)

        # Segurança
        if self.anfir.empty:
            self.anfir = pd.DataFrame(columns=["cliente", "estado", "linha", "segmento"])

        if self.neg.empty:
            self.neg = pd.DataFrame(columns=[
                "cliente", "estado", "produto",
                "status", "valor", "condicao_pagamento"
            ])

    # ------------------------------
    # NORMALIZAÇÃO
    # ------------------------------

    def normalizar(self):

        # ANFIR
        if not self.anfir.empty:
            self.anfir["cliente"] = self.anfir["cliente"].astype(str).str.upper().str.strip()
            self.anfir["linha"] = self.anfir["linha"].astype(str).str.upper().str.strip()

        # NEGOCIAÇÕES
        if not self.neg.empty:
            self.neg["cliente"] = self.neg["cliente"].astype(str).str.upper().str.strip()
            self.neg["produto"] = self.neg["produto"].astype(str).str.upper().str.strip()
            self.neg["status"] = self.neg["status"].astype(str).str.upper().str.strip()

    # ------------------------------
    # MATCH CLIENTE
    # ------------------------------

    def cruzar_dados(self):

        if self.neg.empty:
            return pd.DataFrame()

        # merge por cliente
        merged = pd.merge(
            self.neg,
            self.anfir,
            on="cliente",
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
    # INSIGHT COMERCIAL
    # ------------------------------

    def insights(self):

        self.normalizar()
        base = self.cruzar_dados()

        if base.empty:
            return []

        insights = []

        perdas = base[base["status"] == "PERDIDO"]

        for _, row in perdas.iterrows():

            insight = {
                "cliente": row.get("cliente"),
                "produto_ofertado": row.get("produto"),
                "segmento": row.get("segmento"),
                "estado": row.get("estado"),
                "condicao_pagamento": row.get("condicao_pagamento"),
                "alerta": "Perda identificada — revisar condição comercial"
            }

            insights.append(insight)

        return insights
