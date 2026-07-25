from __future__ import annotations

import re

from core.entity_normalizer import normalizar_entidade

CAMPOS_LINHA = (
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
    "tipo_veiculo",
    "descricao",
    "fabricante_equipamento",
)

ALIASES_LINHA = {
    "TR": {
        "TR", "TRAILER", "CARRETA", "SEMI REBOQUE", "SEMIREBOQUE",
        "SEMI-REBOQUE", "REBOQUE FRIGORIFICO", "CARRETA FRIGORIFICA",
    },
    "DT": {
        "DT", "DIESEL TRUCK", "DIESEL-TRUCK", "TRUCK", "CAMINHAO",
        "CAMINHAO PESADO", "CAMINHAO MEDIO", "UNIDADE DIESEL",
    },
    "DD": {
        "DD", "DIRECT DRIVE", "DIRECT-DRIVE", "ACIONAMENTO DIRETO",
        "ACOPLADO AO MOTOR", "VAN", "FURGAO", "UTILITARIO", "VUC",
    },
}

TERMOS = {
    "DT": (
        "DIESEL TRUCK", "DIESEL-TRUCK", "SUPRA 750", "SUPRA 850", "SUPRA 1150",
        "SUPRA", "UNIDADE DIESEL",
    ),
    "DD": (
        "DIRECT DRIVE", "DIRECT-DRIVE", "CITIMAX", "XARIOS", "D6", "D7",
        "ACOPLADO AO MOTOR", "ACIONAMENTO DIRETO",
    ),
    "TR": (
        "TRAILER", "SEMI REBOQUE", "SEMIREBOQUE", "SEMI-REBOQUE",
        "REBOQUE FRIGORIFICO", "CARRETA FRIGORIFICA", "VECTOR", "X4 7500", "X4 7700",
    ),
}

CODIGOS = ("DT", "DD", "TR")


def texto_linha(registro: dict) -> str:
    partes = [str(registro.get(campo) or "") for campo in CAMPOS_LINHA]
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
    # A base nacional usa frequentemente tipo_veiculo enquanto a Viena usa linha.
    # Todos os campos estruturados devem aceitar a mesma taxonomia controlada.
    for campo in CAMPOS_LINHA:
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
    for campo in ("modelo_equipamento", "modelo", "produto", "linha", "equipamento", "tipo_equipamento", "tipo_veiculo"):
        valor = registro.get(campo)
        if valor not in (None, ""):
            return str(valor).strip()
    return "NÃO INFORMADO"