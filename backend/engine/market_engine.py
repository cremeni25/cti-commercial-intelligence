import pandas as pd

# ============================================================
# PREÇO OFICIAL (TABELA BRUTA)
# ============================================================

PRECO_TABELA = {
    "VECTOR 8500": 178000,
    "VECTOR HE19": 169000,
    "X4 7700": 172000,
    "X4 7500": 158000,

    "SUPRA 750": 105000,
    "SUPRA 850": 113000,
    "SUPRA 1150": 128000,

    "CITIMAX 280": 14500,
    "CITIMAX 400": 18500,
    "CITIMAX 500": 27000,
    "CITIMAX 500 AE": 41000,

    "D6": 28000,
    "D6 AE": 43000,
    "D7": 29000,
    "D7 AE": 45000,

    "XARIOS 350": 43000,
    "XARIOS 6": 53000
}

# ============================================================
# RELAÇÃO SEGMENTO → PRODUTOS
# ============================================================

SEGMENTO_MAP = {
    "TRAILER": [
        "VECTOR 8500", "VECTOR HE19", "X4 7700", "X4 7500"
    ],
    "DIESEL TRUCK": [
        "SUPRA 1150", "SUPRA 850", "SUPRA 750"
    ],
    "DIRECT DRIVE": [
        "CITIMAX 280", "CITIMAX 400", "CITIMAX 500", "CITIMAX 500 AE",
        "D6", "D6 AE", "D7", "D7 AE",
        "XARIOS 350", "XARIOS 6"
    ]
}

# ============================================================
# ENGINE
# ============================================================

class MarketEngine:

    def __init__(self, data):

        self.data = [
            d for d in data
            if d.get("estado") and d.get("segmento")
        ]

        for d in self.data:

            segmento = (d.get("segmento") or "").upper().strip()
            linha = (d.get("linha") or "").upper().strip()

            produtos_validos = SEGMENTO_MAP.get(segmento, [])

            # MATCH EXATO
            if linha in produtos_validos:
                d["valor"] = PRECO_TABELA.get(linha, None)
            else:
                d["valor"] = None  # NÃO INVENTA VALOR

        self.df = pd.DataFrame(self.data)

    # ------------------------------
    # ANALISE REGIONAL
    # ------------------------------

    def regional_analysis(self):

        if self.df.empty:
            return []

        df = self.df.dropna(subset=["valor"])

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

        df = self.df.dropna(subset=["valor"])

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

        df = self.df.dropna(subset=["valor"])

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

        df = self.df.dropna(subset=["valor"])

        regional = df.groupby("estado")["valor"].sum()

        media = regional.mean()

        oportunidades = regional[regional < media]

        return oportunidades.reset_index().to_dict(orient="records")

    # ------------------------------
    # DIAGNÓSTICO ESTRATÉGICO
    # ------------------------------

    def diagnostico_estrategico(self):

        if self.df.empty:
            return {"status": "sem dados"}

        df = self.df.dropna(subset=["valor"])

        if df.empty:
            return {"status": "sem valor válido"}

        total = df["valor"].sum()

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

        df = self.df.dropna(subset=["valor"])

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
    # ORQUESTRADOR
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
