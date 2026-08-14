from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from repositories.cti_repository import repository
from services.base_analytics import consolidar_dashboard
from services.historical_commercial_source import (
    carregar_historico_comercial,
    resumir_historico_comercial,
)
from services.ia_comercial_universo_historico import registrar_historico_comercial_no_universo
from services.operational_filters import data_registro, filtrar_registros

registrar_historico_comercial_no_universo()

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
        "origem_semantica": "CTI_ANFIR",
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
        base_anfir = list(repository.buscar_cti_anfir() or [])
    except Exception:
        base_anfir = []

    contexto = "brasil" if tipo_usuario == "ADMIN_MASTER" else "viena-sp"
    registros_anfir = filtrar_registros(base_anfir, contexto=contexto)
    hoje = date.today()
    inicio_90_dias = hoje - timedelta(days=89)
    recentes_anfir = [
        registro for registro in registros_anfir
        if (data := data_registro(registro)) is not None and inicio_90_dias <= data <= hoje
    ]
    recentes_anfir.sort(key=lambda item: data_registro(item) or date.min, reverse=True)

    try:
        comercial = carregar_historico_comercial()
        resumo_comercial = resumir_historico_comercial(comercial)
    except Exception as exc:
        comercial = ()
        resumo_comercial = {"disponivel": False, "erro": str(exc)}

    pool_consultavel = list(comercial) + [
        _registro_resumido(item) for item in recentes_anfir[:MAX_REGISTROS_RECENTES]
    ]

    return {
        "fonte": "Fontes homologadas CTI/ANFIR + Histórico Comercial 2023–2026",
        "fontes": {
            "cti_anfir": {
                "homologado": True,
                "escopo": contexto,
                "total_registros_escopo": len(registros_anfir),
            },
            "historico_comercial": {
                "homologado": True,
                "total_registros": len(comercial),
                "somente_leitura": True,
                "nao_promove_crm": True,
            },
        },
        "escopo": contexto,
        "periodo_recente": {
            "inicio": inicio_90_dias.isoformat(),
            "fim": hoje.isoformat(),
            "total_registros_anfir": len(recentes_anfir),
        },
        "dashboard_historico": {
            "cti_anfir": consolidar_dashboard(registros_anfir),
            "historico_comercial": resumo_comercial,
        },
        "registros_ultimos_90_dias": pool_consultavel,
        "registros_consultaveis": pool_consultavel,
        "observacao_amostragem": (
            f"Pool semântico: {len(comercial)} registros do histórico comercial homologado e até "
            f"{MAX_REGISTROS_RECENTES} registros recentes CTI/ANFIR. Os resumos usam as bases completas. "
            "O histórico comercial é somente leitura e não cria nem altera Pipeline, Forecast ou CRM ativo."
        ),
    }
