# engine/market_engine.py

import pandas as pd


class MarketEngine:

    def __init__(self, data):

        # ------------------------------
        # FILTRO DE DADOS VÁLIDOS
        # ------------------------------
        self.data = [
            d for d in data
            if d.get("estado") and d.get("linha")
        ]

        # ------------------------------
        # NORMALIZAÇÃO ESTRUTURAL
        # ------------------------------
        for d in self.data:

            d["estado"] = (d.get("estado") or "").upper().strip()
            d["linha"] = (d.get("linha") or "").upper().strip()
            d["implementador"] = (d.get("implementador") or "").upper().strip()

            # ⚠️ VALOR REMOVIDO (ANFIR NÃO POSSUI VALOR REAL)
            d["valor"] = None

        # ------------------------------
        # DATAFRAME
        # ------------------------------
        self.df = pd.DataFrame(self.data)

    # ------------------------------
    # ANALISE REGIONAL
    # ------------------------------

    def regional_analysis(self):

        if self.df.empty:
            return []

        df = self.df.copy()

        # substitui None por 0 apenas para cálculo
        df["valor"] = df["valor"].fillna(0)

        regional = (
            df.groupby("estado")["valor"]
            .sum()
            .reset_index()
            .sort_values("valor", ascending=False)
        )

        return regional.to_dict(orient="records")

    # ------------------------------
    # SHARE POR OEM
    # ------------------------------

    def oem_share(self):

        if self.df.empty:
            return []

        df = self.df.copy()
        df["valor"] = df["valor"].fillna(0)

        total = df["valor"].sum()

        if total == 0:
            return []

        oem = (
            df.groupby("implementador")["valor"]
            .sum()
            .reset_index()
        )

        oem["share"] = (oem["valor"] / total) * 100

        return oem.sort_values("share", ascending=False).to_dict(orient="records")

    # ------------------------------
    # ANALISE POR LINHA
    # ------------------------------

    def product_lines(self):

        if self.df.empty:
            return []

        df = self.df.copy()
        df["valor"] = df["valor"].fillna(0)

        linhas = (
            df.groupby("linha")["valor"]
            .sum()
            .reset_index()
            .sort_values("valor", ascending=False)
        )

        return linhas.to_dict(orient="records")

    # ------------------------------
    # REGIOES SUBEXPLORADAS
    # ------------------------------

    def underperforming_regions(self):

        if self.df.empty:
            return []

        df = self.df.copy()
        df["valor"] = df["valor"].fillna(0)

        regional = df.groupby("estado")["valor"].sum()

        media = regional.mean()

        oportunidades = regional[regional < media]

        return oportunidades.reset_index().to_dict(orient="records")

    # ------------------------------
    # 🧠 DIAGNÓSTICO ESTRATÉGICO
    # ------------------------------

    def diagnostico_estrategico(self):

        if self.df.empty:
            return {
                "status": "sem dados"
            }

        df = self.df.copy()
        df["valor"] = df["valor"].fillna(0)

        total = df["valor"].sum()

        if total == 0:
            return {
                "status": "sem faturamento (ANFIR não possui valores financeiros)"
            }

        regional = df.groupby("estado")["valor"].sum()
        media = regional.mean()

        fortes = regional[regional >= media]
        fracos = regional[regional < media]

        linhas = df.groupby("linha")["valor"].sum()
        top_linhas = linhas.sort_values(ascending=False).head(3)

        return {
            "total_faturamento": float(total),
            "media_regional": float(media),
            "regioes_fortes": fortes.reset_index().to_dict(orient="records"),
            "regioes_fracas": fracos.reset_index().to_dict(orient="records"),
            "top_linhas": top_linhas.reset_index().to_dict(orient="records")
        }

    # ------------------------------
    # DOMINÂNCIA DE MERCADO
    # ------------------------------

    def market_dominance(self):

        if self.df.empty:
            return []

        df = self.df.copy()
        df["valor"] = df["valor"].fillna(0)

        total = df["valor"].sum()

        if total == 0:
            return []

        dominance = (
            df.groupby("implementador")["valor"]
            .sum()
            .reset_index()
        )

        dominance["dominancia"] = (dominance["valor"] / total) * 100

        return dominance.sort_values("dominancia", ascending=False).to_dict(orient="records")

    # ------------------------------
    # ORQUESTRADOR COMPLETO
    # ------------------------------

    def market_intelligence(self):

        return {
            "regional_analysis": self.regional_analysis(),
            "oem_share": self.oem_share(),
            "product_lines": self.product_lines(),
            "underperforming_regions": self.underperforming_regions(),
            "diagnostico": self.diagnostico_estrategico(),
            "market_dominance": self.market_dominance()
        }
