from __future__ import annotations

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
    "TR": (
        " TR ", "TRAILER", "SEMI REBOQUE", "SEMIREBOQUE", "SEMI-REBOQUE",
        "REBOQUE FRIGORIFICO", "CARRETA FRIGORIFICA", "VECTOR", "X4 7500", "X4 7700",
    ),
    "DT": (
        " DT ", "DIESEL TRUCK", "DIESEL-TRUCK", "SUPRA 750", "SUPRA 850", "SUPRA 1150",
        "SUPRA", "UNIDADE DIESEL",
    ),
    "DD": (
        " DD ", "DIRECT DRIVE", "DIRECT-DRIVE", "CITIMAX", "XARIOS", "D6", "D7",
        "ACOPLADO AO MOTOR", "ACIONAMENTO DIRETO",
    ),
}


def texto_linha(registro: dict) -> str:
    partes = [str(registro.get(campo) or "") for campo in CAMPOS_LINHA]
    return f" {normalizar_entidade(' '.join(partes))} "


def classificar_linha(registro: dict) -> str | None:
    texto = texto_linha(registro)
    for codigo, termos in TERMOS.items():
        if any(normalizar_entidade(termo) in texto for termo in termos):
            return codigo
    return None


def modelo_linha(registro: dict) -> str:
    for campo in ("modelo_equipamento", "modelo", "produto", "linha", "equipamento", "tipo_equipamento"):
        valor = registro.get(campo)
        if valor not in (None, ""):
            return str(valor).strip()
    return "NÃO INFORMADO"
