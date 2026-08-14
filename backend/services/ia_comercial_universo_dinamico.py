from __future__ import annotations

from typing import Any

from core.supabase_client import supabase
from services import ia_comercial_universo as base

PREFIXO = "fonte_"


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _slug(fonte_id: str) -> str:
    return f"{PREFIXO}{str(fonte_id).replace('-', '_')}"


def _fontes_publicadas(tipo_usuario: str) -> list[dict[str, Any]]:
    if str(tipo_usuario or "").upper() != "ADMIN_MASTER":
        return []
    try:
        return _dados(
            supabase.table("cti_fontes_universais")
            .select("id,nome_exibicao,nome_arquivo,classificacao_negocio,descricao_semantica,campos_semanticos,escopo_ia,publicado_ia,status_governanca")
            .eq("publicado_ia", True)
            .eq("status_governanca", "PUBLICADO_IA")
            .execute()
        )
    except Exception:
        return []


def _registros_fonte(fonte_id: str) -> list[dict[str, Any]]:
    registros: list[dict[str, Any]] = []
    inicio = 0
    while True:
        lote = _dados(
            supabase.table("cti_fontes_semanticas")
            .select("indice,tipo_registro,conteudo_texto,dados,metadados")
            .eq("fonte_id", fonte_id)
            .order("indice")
            .range(inicio, inicio + 999)
            .execute()
        )
        for item in lote:
            dados = item.get("dados") if isinstance(item.get("dados"), dict) else {}
            metadados = item.get("metadados") if isinstance(item.get("metadados"), dict) else {}
            registros.append(base._sanitizar_registro({
                "indice": item.get("indice"),
                "tipo_registro": item.get("tipo_registro"),
                "conteudo_texto": item.get("conteudo_texto"),
                **dados,
                **{f"meta_{k}": v for k, v in metadados.items()},
            }))
        if len(lote) < 1000:
            break
        inicio += 1000
    return registros


def _dinamicas(tipo_usuario: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str], dict[str, Any]]:
    fontes: dict[str, list[dict[str, Any]]] = {}
    descricoes: dict[str, str] = {}
    metadados: dict[str, Any] = {}
    for fonte in _fontes_publicadas(tipo_usuario):
        nome = _slug(str(fonte.get("id") or ""))
        registros = _registros_fonte(str(fonte.get("id") or ""))
        fontes[nome] = registros
        descricoes[nome] = str(fonte.get("descricao_semantica") or f"Fonte homologada {fonte.get('nome_exibicao') or fonte.get('nome_arquivo')}")
        metadados[nome] = {
            "fonte_id": fonte.get("id"),
            "nome_exibicao": fonte.get("nome_exibicao") or fonte.get("nome_arquivo"),
            "classificacao_negocio": fonte.get("classificacao_negocio"),
            "escopo_ia": fonte.get("escopo_ia"),
            "total_registros": len(registros),
        }
    return fontes, descricoes, metadados


def catalogar_universo_cti(usuario_id: str, tipo_usuario: str) -> dict[str, Any]:
    catalogo = base.catalogar_universo_cti(usuario_id, tipo_usuario)
    fontes, descricoes, metadados = _dinamicas(tipo_usuario)
    for nome, registros in fontes.items():
        campos = base._campos(registros)
        catalogo["fontes"].append({
            "fonte": nome,
            "descricao": descricoes[nome],
            "total_registros_autorizados": len(registros),
            "campos_disponiveis": campos,
            "campos_relacionais_candidatos": [campo for campo in campos if campo.endswith("_id")],
            "origem_dinamica": True,
            "governanca": metadados[nome],
        })
    catalogo.setdefault("escopo", {})["fontes_dinamicas"] = metadados
    catalogo["regra"] = catalogo.get("regra", "") + " Fontes homologadas pelo Back Office são descobertas dinamicamente; não dependem de alteração de código por documento."
    return catalogo


def consultar_universo_cti(usuario_id: str, tipo_usuario: str, *, fonte: str, filtros: list[dict[str, Any]] | None = None, termo: str | None = None, agrupar_por: list[str] | None = None, metricas: list[dict[str, Any]] | None = None, ordenar_por: str | None = None, direcao: str = "desc", limite: int = 50, offset: int = 0) -> dict[str, Any]:
    nome = str(fonte or "").strip()
    fontes, descricoes, metadados = _dinamicas(tipo_usuario)
    if nome not in fontes:
        return base.consultar_universo_cti(usuario_id, tipo_usuario, fonte=nome, filtros=filtros, termo=termo, agrupar_por=agrupar_por, metricas=metricas, ordenar_por=ordenar_por, direcao=direcao, limite=limite, offset=offset)

    registros = fontes[nome]
    filtros_seguros = [item for item in (filtros or []) if isinstance(item, dict)]
    agrupamentos = [str(item) for item in (agrupar_por or []) if str(item).strip()][:3]
    metricas_seguras = [item for item in (metricas or []) if isinstance(item, dict)][:8]
    erro = base._validar_plano_campos(registros, filtros=filtros_seguros, agrupar_por=agrupamentos, metricas=metricas_seguras, ordenar_por=ordenar_por)
    if erro:
        return {"fonte": nome, "descricao": descricoes[nome], "modo": "somente_leitura", "governanca": metadados[nome], **erro}
    filtrados = base._aplicar_filtros(registros, filtros_seguros, termo)
    total_filtrado = len(filtrados)
    if agrupamentos:
        if not metricas_seguras:
            metricas_seguras = [{"operacao": "count", "campo": None, "alias": "quantidade_registros"}]
        saida = base._agregar(filtrados, agrupamentos, metricas_seguras)
    else:
        saida = filtrados
    saida = base._ordenar(saida, ordenar_por, direcao)
    limite = max(1, min(int(limite or 50), 200))
    offset = max(0, int(offset or 0))
    return {
        "fonte": nome,
        "descricao": descricoes[nome],
        "modo": "somente_leitura",
        "governanca": metadados[nome],
        "total_fonte_autorizado": len(registros),
        "total_filtrado": total_filtrado,
        "total_resultado": len(saida),
        "offset": offset,
        "limite": limite,
        "tem_mais": offset + limite < len(saida),
        "campos_disponiveis": base._campos(registros),
        "resultado": saida[offset:offset + limite],
    }
