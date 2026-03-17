import pandas as pd

class MarketEngine:

    def __init__(self, data):
        # limpa dados inválidos
        self.data = [
            d for d in data
            if d.get("estado") and d.get("linha")
        ]

        # garante valor válido
        for d in self.data:
            d["valor"] = d.get("valor") or 0

        # cria dataframe
        self.df = pd.DataFrame(self.data)

    # ------------------------------
    # ANALISE REGIONAL
    # ------------------------------

    def regional_analysis(self):

        if self.df.empty:
            return []

        regional = (
            self.df.groupby("estado")["valor"]
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

        total = self.df["valor"].sum()

        if total == 0:
            return []

        oem = (
            self.df.groupby("implementador")["valor"]
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

        linhas = (
            self.df.groupby("linha")["valor"]
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

        regional = self.df.groupby("estado")["valor"].sum()

        media = regional.mean()

        oportunidades = regional[regional < media]

        return oportunidades.reset_index().to_dict(orient="records")

    # ------------------------------
    # ENGINE COMPLETA (ORQUESTRADOR)
    # ------------------------------

    def market_intelligence(self):

        return {
            "regional_analysis": self.regional_analysis(),
            "oem_share": self.oem_share(),
            "product_lines": self.product_lines(),
            "underperforming_regions": self.underperforming_regions()
        }
