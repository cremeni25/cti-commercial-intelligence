from __future__ import annotations

from . import ia_comercial_ia010_auditoria_patch as _patch

# Fecha as variações narrativas observadas em produção sem alterar a auditoria-base:
# 1) "O que o seu arquivo (Carrier) traz — base de comparação" ativa ANEXO;
# 2) "dados encontrados na web" encerra ANEXO e ativa WEB.
_MARCADORES_ADICIONAIS_ANEXO = (
    "o que o seu arquivo",
    "o que seu arquivo",
    "base de comparação",
    "base de comparacao",
)

_MARCADORES_ADICIONAIS_WEB = (
    "dados encontrados na web",
    "dados encontrados na internet",
    "encontrada na web",
    "encontrado na web",
)

_novos: list[tuple[str, tuple[str, ...]]] = []
for _secao, _marcadores in _patch._MARCADORES_ANEXO:
    if _secao == "ANEXO":
        _marcadores = tuple(dict.fromkeys(tuple(_marcadores) + _MARCADORES_ADICIONAIS_ANEXO))
    elif _secao == "WEB":
        _marcadores = tuple(dict.fromkeys(tuple(_marcadores) + _MARCADORES_ADICIONAIS_WEB))
    _novos.append((_secao, _marcadores))
_patch._MARCADORES_ANEXO = tuple(_novos)
