from __future__ import annotations

import re

from core.entity_normalizer import normalizar_entidade

# Somente campos que descrevem a linha, família, modelo ou equipamento frigorífico.
# `tipo_veiculo` não participa da classificação: caminhão, van, furgão, VUC,
# carreta e semirreboque descrevem o veículo, não determinam TR, DT ou DD.
CAMPOS_EQUIPAMENTO = (
    "segmento",
    "produto",
    "linha",
    "linha_produto",
    "familia",
    "categoria",
    "modelo",
    "modelo_equipamento",
    "equipamento",
    "tipo_equipamento",
    "descricao",
    "fabricante_equipamento",
    "modelo_carrier",
    "modelo_concorrencia",
)

ALIASES_LINHA = {
    "TR": {
        "TR", "TRAILER", "LINHA TRAILER", "EQUIPAMENTO TRAILER",
    },
    "DT": {
        "DT", "DIESEL TRUCK", "DIESEL-TRUCK", "UNIDADE DIESEL",
    },
    "DD": {
        "DD", "DIRECT DRIVE", "DIRECT-DRIVE", "ACIONAMENTO DIRETO",
        "ACOPLADO AO MOTOR",
    },
}

TERMOS = {
    "DT": (
        "DIESEL TRUCK", "DIESEL-TRUCK", "SUPRA 750", "SUPRA 850", "SUPRA 1150",
        "SUPRA", "UNIDADE DIESEL",
    ),
    "DD": (
        "DIRECT DRIVE", "DIRECT-DRIVE", "CITIMAX", "XARIOS", "CM 280", "CM 400",
        "CM 500", "CM 600", "D6", "D7", "ACOPLADO AO MOTOR", "ACIONAMENTO DIRETO",
    ),
    "TR": (
        "LINHA TRAILER", "EQUIPAMENTO TRAILER", "VECTOR", "X4 7500", "X4 7700",
        "X4-7500", "X4-7700", "HE19",
    ),
}

CODIGOS = ("DT", "DD", "TR")


def texto_linha(registro: dict) -> str:
    partes = [str(registro.get(campo) or "") for campo in CAMPOS_EQUIPAMENTO]
    return normalizar_entidade(" ".join(partes))


def _codigo_isolado(texto: str, codigo: str) -> bool:
    return re.search(rf"(?:^|\s){re.escape(codigo)}(?:\s|$)", texto) is not None


def _classificar_valor_exato(valor_bruto) -> str | None:
    valor = normalizar_entidade(str(valor_bruto or "")).strip()
    if not valor:
        return None
    for codigo, aliases in ALIASES_LINHA.items():
        if valor in aliases:
            return codigo
    for codigo in CODIGOS:
        if _codigo_isolado(valor.replace("-", " "), codigo):
            return codigo
    return None


def _classificar_campos_estruturados(registro: dict) -> str | None:
    for campo in CAMPOS_EQUIPAMENTO:
        codigo = _classificar_valor_exato(registro.get(campo))
        if codigo:
            return codigo
    return None


def classificar_linha(registro: dict) -> str | None:
    codigo_estruturado = _classificar_campos_estruturados(registro)
    if codigo_estruturado:
        return codigo_estruturado

    texto = texto_linha(registro)
    for codigo, termos in TERMOS.items():
        if any(normalizar_entidade(termo) in texto for termo in termos):
            return codigo
    for codigo in CODIGOS:
        if _codigo_isolado(texto, codigo):
            return codigo
    return None


def modelo_linha(registro: dict) -> str:
    for campo in (
        "modelo_equipamento", "modelo_carrier", "modelo", "produto", "linha",
        "equipamento", "tipo_equipamento",
    ):
        valor = registro.get(campo)
        if valor not in (None, ""):
            return str(valor).strip()
    return "NÃO INFORMADO"
