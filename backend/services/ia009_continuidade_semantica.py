from __future__ import annotations

import re
import unicodedata


def normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    base = "".join(ch for ch in bruto if not unicodedata.combining(ch)).casefold()
    base = re.sub(r"[^a-z0-9%/_+\-. ]+", " ", base)
    return re.sub(r"\s+", " ", base).strip()


_REFERENCIAS = (
    r"de acordo com (?:a|as|o|os)? ?resposta(?:s)? acima",
    r"com base (?:na|nas|no|nos)? ?resposta(?:s)? acima",
    r"com base no que foi apresentado",
    r"a partir (?:da|das|do|dos)? ?(?:resposta|dados|informacoes|analise|resultado)(?:s)? (?:acima|anterior(?:es)?)",
    r"(?:resposta|dados|informacoes|analise|resultado)(?:s)? (?:acima|anterior(?:es)?)",
    r"utilizando a disposicao (?:da|das|do|dos)? ?resposta(?:s)? apresentad(?:a|as|o|os)",
    r"utilizando (?:a|as|o|os)? ?(?:informacoes|dados) apresentad(?:a|as|o|os)",
)

_ARTEFATOS = (
    r"gere(?: para mim)? (?:um|uma|os|as)? ?grafico(?:s)?",
    r"crie(?: para mim)? (?:um|uma|os|as)? ?grafico(?:s)?",
    r"transforme(?: isso)? em (?:um|uma)? ?grafico(?:s)?",
    r"gere(?: para mim)? (?:um|uma)? ?pdf",
    r"transforme(?: isso)? em (?:um|uma)? ?pdf",
    r"gere(?: para mim)? (?:um|uma|os|as)? ?relatorio(?:s)?",
    r"transforme(?: isso)? em (?:um|uma)? ?relatorio(?:s)?",
    r"disponibilize(?: para)? download",
    r"para baixar",
)

_CONECTORES_APRESENTACAO = (
    "e",
    "tambem",
    "por favor",
    "agora",
    "utilizando",
    "a disposicao",
    "das respostas apresentadas",
    "dos dados apresentados",
    "das informacoes apresentadas",
)


def residual_factual_transformacao(mensagem: str) -> str:
    texto = normalizar(mensagem)
    for padrao in _REFERENCIAS:
        texto = re.sub(padrao, " ", texto)
    for padrao in _ARTEFATOS:
        texto = re.sub(padrao, " ", texto)
    for trecho in _CONECTORES_APRESENTACAO:
        texto = re.sub(rf"\b{re.escape(trecho)}\b", " ", texto)
    texto = re.sub(r"\b(?:um|uma|o|a|os|as|de|do|da|dos|das|no|na|nos|nas|com|em|para)\b", " ", texto)
    return re.sub(r"\s+", " ", texto).strip(" ,.;:-")


def eh_transformacao_pura(mensagem: str) -> bool:
    texto = normalizar(mensagem)
    tem_referencia = any(re.search(padrao, texto) for padrao in _REFERENCIAS)
    tem_artefato = any(re.search(padrao, texto) for padrao in _ARTEFATOS)
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
