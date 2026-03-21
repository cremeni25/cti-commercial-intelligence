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

# ------------------------------
# 🧠 INTELIGÊNCIA DE PERDAS
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

    insights = []

    for _, row in analise.iterrows():

        motivo = row["motivo_perda"]
        qtd = int(row["quantidade"])

        # inteligência simples (evoluiremos depois)
        if "PRAZO" in str(motivo).upper():
            acao = "Revisar política de prazo (possível perda por financiamento)"
        elif "PRECO" in str(motivo).upper():
            acao = "Revisar competitividade de preço"
        elif "ESTOQUE" in str(motivo).upper():
            acao = "Problema de disponibilidade / entrega"
        else:
            acao = "Análise manual necessária"

        insights.append({
            "motivo": motivo,
            "quantidade": qtd,
            "acao_sugerida": acao
        })

    return insights

# ------------------------------
# 🤖 RECOMENDAÇÃO COMERCIAL
# ------------------------------

def recomendacoes(self):

    self.normalizar()
    base = self.cruzar_dados()

    if base.empty:
        return []

    recomendacoes = []

    # analisar perdas
    perdas = base[base["status"] == "PERDIDO"]

    for _, row in perdas.iterrows():

        motivo = str(row.get("motivo_perda", "")).upper()
        segmento = row.get("segmento")
        estado = row.get("estado")

        acao = "Revisar abordagem comercial"

        if "PRAZO" in motivo:
            acao = "Oferecer melhor condição de pagamento (prazo maior)"

        elif "PRECO" in motivo:
            acao = "Avaliar desconto ou reposicionamento de preço"

        elif "ESTOQUE" in motivo or "ENTREGA" in motivo:
            acao = "Priorizar disponibilidade / logística"

        recomendacoes.append({
            "cliente_id": row.get("cliente_id"),
            "estado": estado,
            "segmento": segmento,
            "motivo_perda": motivo,
            "recomendacao": acao
        })

    return recomendacoes
