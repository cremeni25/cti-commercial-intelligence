from __future__ import annotations

from . import ia_comercial_ia010_auditoria_patch as _patch

# Fecha a última variação narrativa observada em produção: títulos como
# "O que o seu arquivo (Carrier) traz — base de comparação" precisam ativar
# o estado ANEXO para que as afirmações seguintes herdem ANEXO_1.
_MARCADORES_ADICIONAIS_ANEXO = (
    "o que o seu arquivo",
    "o que seu arquivo",
    "base de comparação",
    "base de comparacao",
)

_novos: list[tuple[str, tuple[str, ...]]] = []
for _secao, _marcadores in _patch._MARCADORES_ANEXO:
    if _secao == "ANEXO":
        _marcadores = tuple(dict.fromkeys(tuple(_marcadores) + _MARCADORES_ADICIONAIS_ANEXO))
    _novos.append((_secao, _marcadores))
_patch._MARCADORES_ANEXO = tuple(_novos)
