from __future__ import annotations

import re

from core.entity_normalizer import normalizar_entidade

CAMPOS_EQUIPAMENTO = (
    "segmento",
    "produto",
    "linha",
    "linha_produto",
    "familia",
    "categoria",
    "modelo",
    "modelo_carrier",
    "modelo_equipamento",
    "equipamento",
    "tipo_equipamento",
    "descricao",
    "fabricante_equipamento",
)

MODELOS_OFICIAIS = {
    "TR": {
        "X4-7500": ("X4 7500", "X4-7500", "X47500"),
        "X4-7700": ("X4 7700", "X4-7700", "X47700"),
        "VECTOR HE19": ("VECTOR HE19", "HE19", "HE 19"),
    },
    "DT": {
        "SUPRA 750": ("SUPRA 750", "SUPRA750"),
        "SUPRA 850": ("SUPRA 850", "SUPRA850"),
        "SUPRA 1150": ("SUPRA 1150", "SUPRA1150"),
    },
    "DD": {
        "CM280": ("CM280", "CM 280", "CM-280"),
        "CM400": ("CM400", "CM 400", "CM-400"),
        "CM500": ("CM500", "CM 500", "CM-500"),
        "CM500AE": ("CM500AE", "CM 500 AE", "CM-500-AE", "CM500 AE"),
        "D6": ("D6", "D 6"),
        "D6AE": ("D6AE", "D6 AE", "D 6 AE"),
        "D7": ("D7", "D 7"),
        "D7AE": ("D7AE", "D7 AE", "D 7 AE"),
        "XARIOS 350": ("XARIOS 350", "XARIOS350"),
        "XARIOS 600": ("XARIOS 600", "XARIOS600"),
    },
}

ALIASES_LINHA = {
    "TR": {"TR", "TRAILER", "LINHA TRAILER"},
    "DT": {"DT", "DIESEL TRUCK", "DIESEL-TRUCK", "LINHA DIESEL TRUCK", "UNIDADE DIESEL"},
    "DD": {"DD", "DIRECT DRIVE", "DIRECT-DRIVE", "ACIONAMENTO DIRETO", "ACOPLADO AO MOTOR"},
}

CODIGOS = ("DT", "DD", "TR")


def _texto_equipamento(registro: dict) -> str:
    partes = [str(registro.get(campo) or "") for campo in CAMPOS_EQUIPAMENTO]
    return normalizar_entidade(" ".join(partes))


def _codigo_isolado(texto: str, codigo: str) -> bool:
    return re.search(rf"(?:^|\s){re.escape(codigo)}(?:\s|$)", texto) is not None


def _contem_alias(texto: str, alias: str) -> bool:
    alias_normalizado = normalizar_entidade(alias)
    return re.search(rf"(?:^|\s){re.escape(alias_normalizado)}(?:\s|$)", texto) is not None


def _aliases_modelos_ordenados() -> list[tuple[int, str, str, str]]:
    candidatos: list[tuple[int, str, str, str]] = []
    for linha, modelos in MODELOS_OFICIAIS.items():
        for canonico, aliases in modelos.items():
            for alias in aliases:
                alias_normalizado = normalizar_entidade(alias)
                candidatos.append((len(alias_normalizado), linha, canonico, alias))
    return sorted(candidatos, key=lambda item: item[0], reverse=True)


ALIASES_MODELOS_ORDENADOS = _aliases_modelos_ordenados()


def modelo_oficial(registro: dict) -> tuple[str, str] | None:
    """Retorna (linha, modelo canônico) apenas quando há evidência de equipamento."""
    texto = _texto_equipamento(registro)
    if not texto:
        return None
    # Modelos com sufixos ou variantes específicas devem ser avaliados antes dos
    # modelos-base. Ex.: D6AE antes de D6, D7AE antes de D7 e CM500AE antes de CM500.
    for _, linha, canonico, alias in ALIASES_MODELOS_ORDENADOS:
        if _contem_alias(texto, alias):
            return linha, canonico
    return None


def _classificar_linha_explicita(registro: dict) -> str | None:
    for campo in ("linha", "linha_produto", "familia", "categoria", "segmento"):
        valor = normalizar_entidade(str(registro.get(campo) or "")).strip()
        if not valor:
            continue
        for codigo, aliases in ALIASES_LINHA.items():
            if valor in aliases or _codigo_isolado(valor.replace("-", " "), codigo):
                return codigo
    return None


def classificar_linha(registro: dict) -> str | None:
    modelo = modelo_oficial(registro)
    if modelo:
        return modelo[0]
    return _classificar_linha_explicita(registro)


def modelo_linha(registro: dict) -> str:
    modelo = modelo_oficial(registro)
    return modelo[1] if modelo else "NÃO INFORMADO"
