# ============================================================
# CTI NORMALIZADOR UNIVERSAL
# ============================================================

import pandas as pd
import io
import re
from datetime import datetime

# ============================================================
# NORMALIZAÇÃO BASE
# ============================================================

def limpar_texto(txt):
    if not txt:
        return ""
    return str(txt).strip().upper()


def limpar_numero(v):
    try:
        if v is None:
            return 0
        return float(str(v).replace(".", "").replace(",", "."))
    except:
        return 0


# ============================================================
# DETECÇÃO FLEXÍVEL DE CAMPOS
# ============================================================

def detectar_campo(linha, nomes):
    for k in linha.keys():
        for n in nomes:
            if n in k:
                return linha.get(k)
    return None


# ============================================================
# NORMALIZADOR PRINCIPAL
# ============================================================

def normalizar_planilha(contents, origem="upload"):

    dfs = pd.read_excel(io.BytesIO(contents), sheet_name=None)

    registros = []

    for nome_aba, df in dfs.items():

        df = df.fillna("")
        df.columns = [str(c).strip().lower() for c in df.columns]

        for _, row in df.iterrows():

            linha = {str(k).lower(): v for k, v in row.items()}

            cliente = detectar_campo(linha, ["cliente", "razao", "empresa", "nome"])
            cnpj = detectar_campo(linha, ["cnpj", "cpf"])
            cidade = detectar_campo(linha, ["cidade", "municipio"])
            estado = detectar_campo(linha, ["estado", "uf"])
            valor = detectar_campo(linha, ["valor", "total", "preco"])
            data = detectar_campo(linha, ["data", "emissao"])

            registro = {
                "cliente": limpar_texto(cliente),
                "cnpj": re.sub(r"\D", "", str(cnpj)) if cnpj else None,
                "cidade": limpar_texto(cidade),
                "estado": limpar_texto(estado),
                "valor": limpar_numero(valor),
                "data": str(data),
                "origem": f"{origem}_{nome_aba}",
                "created_at": datetime.utcnow().isoformat()
            }

            # 🔥 REGRA: NÃO DESCARTA DADOS
            if not any([
                registro["cliente"],
                registro["cnpj"],
                registro["valor"]
            ]):
                continue

            registros.append(registro)

    return registros
