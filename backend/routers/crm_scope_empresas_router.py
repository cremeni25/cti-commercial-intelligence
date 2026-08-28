from __future__ import annotations

from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_atividades_router import _filtrar_agenda
from routers.crm_scope_estrategia_router import _anfir_do_usuario, _metadata_escopo
from routers.crm_scope_router import _filtrar_por_usuario
from routers.crm_router import listar_oportunidades
from routers.documentos_comerciais_listagem_router import listar_pedidos_operacionais, listar_propostas_operacionais
from routers.negociacoes_router import agenda_comercial
from services.base_analytics import valor_float
from routers.modulos_router import _nome_empresa, _valor_texto

router = APIRouter(prefix="/crm-seguro/empresas", tags=["crm-seguro-empresas"])


def _consolidar(registros: list[dict]) -> list[dict]:
    agrupado: dict[str, dict] = {}
    for registro in registros:
        nome = _nome_empresa(registro)
        if not nome:
            continue
        chave = nome.upper()
        item = agrupado.setdefault(chave, {
            "nome": nome,
            "quantidade_registros": 0,
            "valor_total": 0.0,
            "estados": set(),
            "municipios": set(),
            "linhas": set(),
            "status": Counter(),
            "chassis": set(),
            "placas": set(),
            "implementadoras": set(),
            "equipamentos": set(),
        })
        item["quantidade_registros"] += 1
        item["valor_total"] += valor_float(registro.get("valor"))
        for campo_destino, candidatos in (
            ("estados", ("estado", "uf")),
            ("municipios", ("cidade", "municipio")),
            ("linhas", ("linha", "produto")),
            ("chassis", ("chassi",)),
            ("placas", ("placa",)),
            ("implementadoras", ("implementadora", "implementador")),
            ("equipamentos", ("modelo_equipamento", "modelo", "linha", "produto")),
        ):
            valor = _valor_texto(registro, *candidatos)
            if valor:
                item[campo_destino].add(valor)
        item["status"][registro.get("status") or "OUTROS"] += 1

    saida = []
    for item in agrupado.values():
        item["valor_total"] = round(item["valor_total"], 2)
        for campo in ("estados", "municipios", "linhas", "chassis", "placas", "implementadoras", "equipamentos"):
            item[campo] = sorted(item[campo])
        item["quantidade_chassis"] = len(item["chassis"])
        item["quantidade_placas"] = len(item["placas"])
        item["status"] = dict(item["status"])
        saida.append(item)
    return sorted(saida, key=lambda item: item["quantidade_registros"], reverse=True)


@router.get("")
def listar_empresas_seguras(
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    registros, inicio_efetivo, fim_efetivo = _anfir_do_usuario(usuario, contexto, periodo, uf, ddd, inicio, fim)
    return {
        "itens": _consolidar(registros),
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
            "escopo_usuario": _metadata_escopo(usuario),
        },
    }


@router.get("/crm-resumo")
def crm_resumo_seguro(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    oportunidades = _filtrar_por_usuario(listar_oportunidades(), usuario)
    propostas = _filtrar_por_usuario(listar_propostas_operacionais(), usuario)
    pedidos = _filtrar_por_usuario(listar_pedidos_operacionais(), usuario)
    agenda = _filtrar_agenda(agenda_comercial(), usuario)
    return {
        "oportunidades": oportunidades,
        "propostas": propostas,
        "pedidos": pedidos,
        "atividades": list(agenda.get("itens") or []),
    }
