from __future__ import annotations

import re
import unicodedata


def normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    base = "".join(ch for ch in bruto if not unicodedata.combining(ch)).casefold()
    base = re.sub(r"[^a-z0-9%/_+\-. ]+", " ", base)
    return re.sub(r"\s+", " ", base).strip()


_TOKENS_APRESENTACAO = {
    "a", "acima", "acordo", "agora", "analise", "anterior", "anteriores", "apresentada", "apresentadas", "apresentado", "apresentados",
    "as", "base", "baixar", "com", "crie", "da", "das", "dados", "de", "disponibilize", "disposicao", "do", "dos", "download", "e",
    "em", "gere", "grafico", "graficos", "informacoes", "isso", "me", "mim", "na", "nas", "no", "nos", "o", "os", "para", "partir",
    "pdf", "por", "relatorio", "relatorios", "resposta", "respostas", "resultado", "resultados", "tambem", "transforme", "um", "uma", "utilizando",
}

_REFERENCIAS_EXPLICITAS = (
    "resposta acima",
    "respostas acima",
    "resposta anterior",
    "respostas anteriores",
    "dados apresentados",
    "informacoes apresentadas",
    "analise acima",
    "resultado acima",
    "com base no que foi apresentado",
    "disposicao das respostas apresentadas",
)

_ARTEFATOS = {"grafico", "graficos", "pdf", "relatorio", "relatorios"}


def _tokens(texto: str) -> list[str]:
    return re.findall(r"[a-z0-9%/_+\-.]+", normalizar(texto))


def residual_factual_transformacao(mensagem: str) -> str:
    restantes = [token for token in _tokens(mensagem) if token not in _TOKENS_APRESENTACAO]
    return " ".join(restantes)


def eh_transformacao_pura(mensagem: str) -> bool:
    texto = normalizar(mensagem)
    tokens = set(_tokens(texto))
    tem_referencia = any(ref in texto for ref in _REFERENCIAS_EXPLICITAS)
    tem_artefato = bool(tokens & _ARTEFATOS)
    if not (tem_referencia and tem_artefato):
        return False
    return residual_factual_transformacao(mensagem) == ""


def pediu_atualizacao_explicita(mensagem: str) -> bool:
    texto = normalizar(mensagem)
    sinais = (
        "atualize",
        "atualizar",
        "nova pesquisa",
        "pesquise novamente",
        "refaca a pesquisa",
        "refazer a pesquisa",
        "consulte novamente",
        "dados atualizados",
        "dados mais recentes",
    )
    return any(sinal in texto for sinal in sinais)
