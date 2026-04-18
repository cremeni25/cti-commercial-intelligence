# cti_id_inteligente.py — versão completa e final

import hashlib
import re


def limpar_texto(texto):
    if not texto:
        return ""
    texto = str(texto).upper().strip()
    texto = re.sub(r'[^A-Z0-9 ]', '', texto)
    return texto


def gerar_hash(valor: str) -> str:
    return hashlib.md5(valor.encode()).hexdigest()


def gerar_id_cliente(row: dict) -> str:
    """
    Gera ID único inteligente baseado em prioridade:
    1. CNPJ
    2. Nome + Cidade + Estado
    3. Fallback com hash geral
    """

    cnpj = limpar_texto(row.get("cnpj"))
    cliente = limpar_texto(row.get("cliente"))
    cidade = limpar_texto(row.get("cidade"))
    estado = limpar_texto(row.get("estado"))

    if cnpj:
        return f"CNPJ_{cnpj}"

    if cliente and cidade and estado:
        base = f"{cliente}_{cidade}_{estado}"
        return f"NOME_{gerar_hash(base)}"

    base = f"{cliente}_{cidade}_{estado}_{row.get('valor', '')}"
    return f"GEN_{gerar_hash(base)}"


def gerar_id_linha(row: dict) -> str:
    """
    ID único por linha (transação)
    """
    base = f"{row.get('cliente')}_{row.get('data')}_{row.get('valor')}"
    return gerar_hash(base)
