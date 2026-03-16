import pandas as pd

class MarketEngine:

    def __init__(self, data):
        self.df = pd.DataFrame(data)

    # ------------------------------
    # ANALISE REGIONAL
    # ------------------------------

    def regional_analysis(self):

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

        total = self.df["valor"].sum()

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

        regional = self.df.groupby("estado")["valor"].sum()

        media = regional.mean()

        oportunidades = regional[regional < media]

        return oportunidades.reset_index().to_dict(orient="records")
