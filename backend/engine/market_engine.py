# engine/market_engine.py

import pandas as pd

PRECO_TABELA = {
    "VECTOR": 178000,
    "VECTOR HE19": 169000,
    "X47700": 172000,
    "X4 7500": 158000,

    "SUPRA 750": 105000,
    "SUPRA 850": 113000,
    "SUPRA 1150": 128000,

    "CITIMAX 280": 14500,
    "CITIMAX 400": 18500,
    "CITIMAX 500 ACOPLADO": 27000,
    "CITIMAX 500 ACOP / ELÉTRICO": 41000,
    "CITIMAX 600 ACOPLADO": 28000,
    "CITIMAX 600 ACOP / ELÉTRICO": 43000,
    "CITIMAX 700 ACOPLADO": 29000,
    "CITIMAX 700 ACOP / ELÉTRICO": 45000,

    "XARIOS 350": 43000,
    "XARIOS 6": 53000
}

class MarketEngine:

    def __init__(self, data):

        self.data = [
            d for d in data
            if d.get("estado") and d.get("linha")
        ]

        for d in self.data:

            linha = (d.get("linha") or "").upper().strip()

            d["valor"] = PRECO_TABELA.get(linha, 0)

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
    # 🧠 NOVO — DIAGNÓSTICO ESTRATÉGICO
    # ------------------------------

    def diagnostico_estrategico(self):

        if self.df.empty:
            return {
                "status": "sem dados"
            }

        total = self.df["valor"].sum()

        if total == 0:
            return {
                "status": "sem faturamento"
            }

        # REGIÕES FORTES
        regional = self.df.groupby("estado")["valor"].sum()
        media = regional.mean()

        fortes = regional[regional >= media]
        fracos = regional[regional < media]

        # LINHAS FORTES
        linhas = self.df.groupby("linha")["valor"].sum()
        top_linhas = linhas.sort_values(ascending=False).head(3)

        return {
            "total_faturamento": float(total),
            "media_regional": float(media),
            "regioes_fortes": fortes.reset_index().to_dict(orient="records"),
            "regioes_fracas": fracos.reset_index().to_dict(orient="records"),
            "top_linhas": top_linhas.reset_index().to_dict(orient="records")
        }

    # ------------------------------
    # ORQUESTRADOR COMPLETO
    # ------------------------------

    def market_intelligence(self):

        return {
            "regional_analysis": self.regional_analysis(),
            "oem_share": self.oem_share(),
            "product_lines": self.product_lines(),
            "underperforming_regions": self.underperforming_regions(),
            "diagnostico": self.diagnostico_estrategico()
        }

def market_dominance(self):

    if self.df.empty:
        return []

    total = self.df["valor"].sum()

    if total == 0:
        return []

    dominance = (
        self.df.groupby("implementador")["valor"]
        .sum()
        .reset_index()
    )

    dominance["dominancia"] = (dominance["valor"] / total) * 100

    return dominance.sort_values("dominancia", ascending=False).to_dict(orient="records")
