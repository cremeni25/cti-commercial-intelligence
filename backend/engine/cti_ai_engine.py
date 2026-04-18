# ============================================================
# CTI AI ENGINE — VERSÃO EXECUTÁVEL
# ============================================================

from typing import Dict, Any

# ============================================================
# PLAYERS DE MERCADO (BASE FIXA DO CTI)
# ============================================================

PLAYERS_MERCADO = [
    "carrier",
    "thermo king",
    "rodofrio",
    "frigoking",
    "thermostar"
]

# ============================================================
# INTERPRETAÇÃO DE PERGUNTA
# ============================================================

def interpretar_pergunta(pergunta: str) -> str:

    pergunta = pergunta.lower()

    # 🔵 dados internos
    if any(p in pergunta for p in [
        "meu", "minha", "meus",
        "cliente", "venda", "faturamento",
        "região", "ddd", "bairro",
        "performance", "resultado"
    ]):
        return "INTERNO"

    # 🌐 mercado
    if any(p in pergunta for p in [
        "mercado", "concorrente", "tendência",
        *PLAYERS_MERCADO
    ]):
        return "WEB"

    # 🧠 híbrido
    return "HIBRIDO"


# ============================================================
# DADOS INTERNOS (INTEGRAÇÃO FUTURA COM SUPABASE)
# ============================================================

def analisar_dados_internos(pergunta: str, dados: Dict = None):

    # 🔥 Aqui depois entra Supabase / banco real

    return {
        "tipo": "analise_interna",
        "insight": f"Análise interna baseada na pergunta: {pergunta}",
        "status": "pendente integração banco"
    }


# ============================================================
# BUSCA WEB (BASE PARA EVOLUÇÃO)
# ============================================================

def buscar_informacao_web(pergunta: str):

    return {
        "tipo": "analise_mercado",
        "players_considerados": PLAYERS_MERCADO,
        "resumo": f"Informações de mercado sobre: {pergunta}",
        "status": "pendente integração web real"
    }


# ============================================================
# MOTOR CENTRAL (ORQUESTRADOR)
# ============================================================

def gerar_resposta(pergunta: str, dados_internos: Dict = None):

    tipo = interpretar_pergunta(pergunta)

    if tipo == "INTERNO":
        return analisar_dados_internos(pergunta, dados_internos)

    elif tipo == "WEB":
        return buscar_informacao_web(pergunta)

    elif tipo == "HIBRIDO":

        interno = analisar_dados_internos(pergunta, dados_internos)
        externo = buscar_informacao_web(pergunta)

        return {
            "tipo": "analise_hibrida",
            "interno": interno,
            "mercado": externo
        }
