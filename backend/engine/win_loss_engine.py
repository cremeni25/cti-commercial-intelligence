# engine/win_loss_engine.py

import pandas as pd

class WinLossEngine:

    def __init__(self, anf_ir_data, negociacoes_data):

        self.anfir = pd.DataFrame(anf_ir_data)
        self.neg = pd.DataFrame(negociacoes_data)

        if self.anfir.empty:
            self.anfir = pd.DataFrame(columns=["cliente_id", "estado", "linha", "segmento"])

        if self.neg.empty:
            self.neg = pd.DataFrame(columns=[
                "cliente_id", "produto", "status",
                "valor_estimado", "motivo_perda"
            ])

    # ------------------------------
    def normalizar(self):

        if not self.neg.empty:
            self.neg["status"] = self.neg["status"].astype(str).str.upper().str.strip()
            self.neg["produto"] = self.neg["produto"].astype(str).str.upper().str.strip()

    # ------------------------------
    def cruzar_dados(self):

        if self.neg.empty:
            return pd.DataFrame()

        return pd.merge(
            self.neg,
            self.anfir,
            on="cliente_id",
            how="left",
            suffixes=("_neg", "_anfir")
        )

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

        return {
            "resumo": {
                "total_negociacoes": int(total),
                "ganhos": int(len(ganhos)),
                "perdas": int(len(perdas)),
                "taxa_conversao": round((len(ganhos) / total * 100), 2) if total > 0 else 0
            },
            "detalhado": base.fillna("").to_dict(orient="records")
        }

    # ------------------------------
    def insights(self):

        self.normalizar()
        base = self.cruzar_dados()

        if base.empty:
            return []

        perdas = base[base["status"] == "PERDIDO"]

        insights = []

        for _, row in perdas.iterrows():

            insights.append({
                "cliente_id": row.get("cliente_id"),
                "produto": row.get("produto"),
                "estado": row.get("estado", ""),
                "segmento": row.get("segmento", ""),
                "valor_estimado": row.get("valor_estimado"),
                "motivo_perda": row.get("motivo_perda"),
                "alerta": "Perda — revisar estratégia comercial"
            })

        return insights

    # ------------------------------
    def analise_perdas(self):

        self.normalizar()
        base = self.cruzar_dados()

        if base.empty:
            return []

        perdas = base[base["status"] == "PERDIDO"]

        if perdas.empty:
            return []

        analise = (
            perdas.groupby("motivo_perda")
            .size()
            .reset_index(name="quantidade")
            .sort_values("quantidade", ascending=False)
        )

        resultado = []

        for _, row in analise.iterrows():

            motivo = row["motivo_perda"]
            qtd = int(row["quantidade"])

            if "PRAZO" in str(motivo).upper():
                acao = "Revisar política de prazo"
            elif "PRECO" in str(motivo).upper():
                acao = "Revisar competitividade de preço"
            elif "ESTOQUE" in str(motivo).upper():
                acao = "Problema de disponibilidade"
            else:
                acao = "Análise manual"

            resultado.append({
                "motivo": motivo,
                "quantidade": qtd,
                "acao_sugerida": acao
            })

        return resultado

    # ------------------------------
    def recomendacoes(self):

        self.normalizar()
        base = self.cruzar_dados()

        if base.empty:
            return []

        perdas = base[base["status"] == "PERDIDO"]

        recomendacoes = []

        for _, row in perdas.iterrows():

            motivo = str(row.get("motivo_perda", "")).upper()

            acao = "Revisar abordagem comercial"

            if "PRAZO" in motivo:
                acao = "Oferecer melhor condição de pagamento"
            elif "PRECO" in motivo:
                acao = "Avaliar política de preço"
            elif "ESTOQUE" in motivo:
                acao = "Ajustar disponibilidade/logística"

            recomendacoes.append({
                "cliente_id": row.get("cliente_id"),
                "estado": row.get("estado", ""),
                "segmento": row.get("segmento", ""),
                "motivo_perda": motivo,
                "recomendacao": acao
            })

        return recomendacoes
