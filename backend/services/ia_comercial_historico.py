from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from repositories.cti_repository import repository
from services.base_analytics import consolidar_dashboard
from services.operational_filters import data_registro, filtrar_registros

MAX_REGISTROS_RECENTES = 160


def _texto(registro: dict[str, Any], *campos: str) -> str | None:
    for campo in campos:
        valor = registro.get(campo)
        if valor not in (None, ""):
            texto = str(valor).strip()
            if texto:
                return texto
    return None


def _registro_resumido(registro: dict[str, Any]) -> dict[str, Any]:
    data = data_registro(registro)
    return {
        "data": data.isoformat() if data else None,
        "cliente": _texto(registro, "cliente", "razao_social", "nome_cliente", "nome"),
        "linha": _texto(registro, "linha", "linha_produto", "familia"),
        "modelo": _texto(registro, "modelo", "produto", "equipamento", "modelo_equipamento"),
        "implementadora": _texto(registro, "implementadora"),
        "autorizado": _texto(registro, "autorizado", "dealer"),
        "estado": _texto(registro, "estado", "uf"),
        "cidade": _texto(registro, "cidade", "municipio"),
        "ddd": _texto(registro, "ddd", "codigo_ddd"),
        "status": _texto(registro, "status"),
        "valor": registro.get("valor"),
        "origem_base": _texto(registro, "origem_base"),
    }


def contexto_historico(tipo_usuario: str) -> dict[str, Any]:
    try:
        base = list(repository.buscar_cti_anfir() or [])
    except Exception:
        base = []

    contexto = "brasil" if tipo_usuario == "ADMIN_MASTER" else "viena-sp"
    registros = filtrar_registros(base, contexto=contexto)
    hoje = date.today()
    inicio_90_dias = hoje - timedelta(days=89)
    recentes = [
        registro for registro in registros
        if (data := data_registro(registro)) is not None and inicio_90_dias <= data <= hoje
    ]
    recentes.sort(key=lambda item: data_registro(item) or date.min, reverse=True)

    return {
        "fonte": "Base histórica CTI/ANFIR usada pelo Dashboard Executivo",
        "escopo": contexto,
        "periodo_recente": {
            "inicio": inicio_90_dias.isoformat(),
            "fim": hoje.isoformat(),
            "total_registros": len(recentes),
        },
        "dashboard_historico": consolidar_dashboard(registros),
        "registros_ultimos_90_dias": [
            _registro_resumido(item) for item in recentes[:MAX_REGISTROS_RECENTES]
        ],
        "observacao_amostragem": (
            f"Foram enviados ao modelo até {MAX_REGISTROS_RECENTES} registros recentes, "
            "ordenados da data mais nova para a mais antiga. As contagens do dashboard usam a base completa."
        ),
    }
