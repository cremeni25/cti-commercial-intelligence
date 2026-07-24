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


def classificar_linha(registro: dict) -> str | None:
    texto = texto_linha(registro)

    # Primeiro reconhece nomenclaturas e modelos completos, evitando que
    # códigos curtos sejam encontrados dentro de palavras como TRUCK.
    for codigo, termos in TERMOS.items():
        if any(normalizar_entidade(termo) in texto for termo in termos):
            return codigo

    for codigo in CODIGOS:
        if _codigo_isolado(texto, codigo):
            return codigo

    return None


def modelo_linha(registro: dict) -> str:
    for campo in ("modelo_equipamento", "modelo", "produto", "linha", "equipamento", "tipo_equipamento"):
        valor = registro.get(campo)
        if valor not in (None, ""):
            return str(valor).strip()
    return "NÃO INFORMADO"
