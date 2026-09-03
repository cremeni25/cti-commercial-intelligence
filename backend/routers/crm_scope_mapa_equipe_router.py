from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers import strategic_layers_router as estrategia
from routers.crm_scope_estrategia_router import FECHADOS, PERFIS_REGIONAIS, _consolidado, _metadata_escopo
from services.commercial_client_scope import filtrar_carteira_exata_responsavel
from services.crm_live_projection import carregar_oportunidades_enriquecidas
from services.historical_commercial_source import carregar_historico_comercial
from services.product_line_classifier import classificar_linha

router = APIRouter(prefix="/crm-seguro/mapa-equipe", tags=["crm-seguro-mapa-equipe"])
PERFIS_ANALISE = PERFIS_REGIONAIS | {"ADMIN_MASTER", "DIRETOR_VIENA_SP"}


def _fold(valor: Any) -> str:
    texto = str(valor or "").strip().upper()
    return " ".join(texto.split())


def _pode_gerir(usuario: UsuarioAutenticado) -> bool:
    return _consolidado(usuario) or usuario.tipo_usuario == "DIRETOR_VIENA_SP"


def _equipe_ativa() -> list[dict[str, Any]]:
    try:
        dados = (
            supabase.table("cti_users")
            .select("id,nome,email,tipo_usuario,ddds,codigo_regional,ativo")
            .eq("ativo", True)
            .execute()
            .data
            or []
        )
    except Exception:
        dados = []
    equipe = [item for item in dados if str(item.get("tipo_usuario") or "").upper() in PERFIS_ANALISE]
    return sorted(equipe, key=lambda item: str(item.get("nome") or ""))


def _usuario_regional(registro: dict[str, Any]) -> UsuarioAutenticado:
    return UsuarioAutenticado(
        id=str(registro.get("id") or ""),
        auth_id="",
        email=str(registro.get("email") or ""),
        nome=str(registro.get("nome") or ""),
        tipo_usuario=str(registro.get("tipo_usuario") or "USUARIO_CTI").upper(),
        permissoes={},
    )


def _resolver_alvo(usuario: UsuarioAutenticado, responsavel_id: str | None) -> tuple[UsuarioAutenticado | None, list[dict[str, Any]]]:
    equipe = _equipe_ativa()
    if not _pode_gerir(usuario):
        return usuario, [item for item in equipe if str(item.get("id")) == str(usuario.id)]
    if not responsavel_id:
        return None, equipe
    registro = next((item for item in equipe if str(item.get("id")) == str(responsavel_id)), None)
    if not registro:
        raise HTTPException(status_code=404, detail="Responsável comercial não encontrado ou fora do escopo de análise.")
    return _usuario_regional(registro), equipe


def _familias(registros: list[dict[str, Any]]) -> dict[str, int]:
    contagem = Counter(classificar_linha(item) for item in registros)
    return {
        "trailer": int(contagem.get("TR", 0)),
        "diesel_truck": int(contagem.get("DT", 0)),
        "direct_drive": int(contagem.get("DD", 0)),
    }


def _nome_cliente_anfir(item: dict[str, Any]) -> str:
    return _fold(item.get("cliente") or item.get("empresa") or item.get("transportadora"))


def _nome_cliente_historico(item: dict[str, Any]) -> str:
    return _fold(item.get("cliente") or item.get("empresa") or item.get("transportadora"))


def _nome_cliente_crm(item: dict[str, Any]) -> str:
    return _fold(item.get("cliente_nome") or item.get("cliente") or item.get("empresa"))


def _clientes(registros: list[dict[str, Any]], extrator) -> set[str]:
    return {nome for item in registros if (nome := extrator(item))}


def _ranking(counter: Counter, limite: int = 8) -> list[dict[str, Any]]:
    return [{"nome": str(nome), "quantidade": int(qtd)} for nome, qtd in counter.most_common(limite) if nome]


def _historico_base(inicio: date, fim: date) -> list[dict[str, Any]]:
    return [
        item
        for item in carregar_historico_comercial()
        if estrategia._data_no_intervalo(item.get("data"), inicio, fim)
    ]


def _carteira_canonica(alvo: UsuarioAutenticado, registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return filtrar_carteira_exata_responsavel(list(registros), str(alvo.id), alvo.nome)


def _historico_carteira(alvo: UsuarioAutenticado, historico_base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _carteira_canonica(alvo, historico_base)


def _crm_carteira(alvo: UsuarioAutenticado, crm_base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _carteira_canonica(alvo, crm_base)


def _anfir_carteira(alvo: UsuarioAutenticado, mercado_total: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _carteira_canonica(alvo, mercado_total)


def _chave_registro(item: dict[str, Any], indice: int) -> str:
    for campo in ("id", "registro_id", "anfir_id", "oportunidade_id"):
        valor = item.get(campo)
        if valor not in (None, ""):
            return f"{campo}:{valor}"
    partes = [
        str(item.get("cliente") or item.get("cliente_nome") or item.get("empresa") or item.get("transportadora") or ""),
        str(item.get("implementadora") or ""),
        str(item.get("equipamento") or item.get("modelo") or ""),
        str(item.get("data") or item.get("mes") or ""),
        str(item.get("quantidade") or ""),
        str(indice),
    ]
    return "|".join(partes)


def _deduplicar(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    saida: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for indice, item in enumerate(registros):
        chave = _chave_registro(item, indice)
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(item)
    return saida


def _agregar_equipe(
    equipe: list[dict[str, Any]],
    mercado_total: list[dict[str, Any]],
    historico_base: list[dict[str, Any]],
    crm_base: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    anf_todos: list[dict[str, Any]] = []
    hist_todos: list[dict[str, Any]] = []
    crm_todos: list[dict[str, Any]] = []
    participacoes: list[dict[str, Any]] = []
    soma_individual = 0

    for registro in equipe:
        alvo = _usuario_regional(registro)
        anf_individual = _anfir_carteira(alvo, mercado_total)
        hist_individual = _historico_carteira(alvo, historico_base)
        crm_individual = _crm_carteira(alvo, crm_base)
        soma_individual += len(anf_individual)
        anf_todos.extend(anf_individual)
        hist_todos.extend(hist_individual)
        crm_todos.extend(crm_individual)
        participacoes.append({
            "id": alvo.id,
            "nome": alvo.nome,
            "mercado": len(anf_individual),
        })

    return (
        _deduplicar(anf_todos),
        _deduplicar(hist_todos),
        _deduplicar(crm_todos),
        participacoes,
        soma_individual,
    )


@router.get("/visao")
def visao_equipe(
    responsavel_id: str | None = None,
    contexto: str = "viena-sp",
    periodo: str = "PERSONALIZADO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    alvo, equipe = _resolver_alvo(usuario, responsavel_id)

    inicio_efetivo = date(2026, 1, 1)
    fim_efetivo = date(2026, 12, 31)
    contexto_efetivo = "viena-sp"
    periodo_efetivo = "PERSONALIZADO"

    mercado_total, _, _ = estrategia._anfir(
        contexto_efetivo,
        periodo_efetivo,
        None,
        None,
        inicio_efetivo,
        fim_efetivo,
    )
    historico_base = _historico_base(inicio_efetivo, fim_efetivo)
    crm_base = carregar_oportunidades_enriquecidas()

    participacoes_equipe: list[dict[str, Any]] = []
    soma_individual = 0

    if alvo is None:
        anf, historico, crm, participacoes_equipe, soma_individual = _agregar_equipe(
            equipe,
            list(mercado_total),
            historico_base,
            crm_base,
        )
        selecao = {"modo": "TODA_EQUIPE", "id": None, "nome": "Toda a equipe comercial", "codigo_regional": None, "ddds": []}
        escopo = {"modo": "TODA_EQUIPE", "usuario": "Toda a equipe comercial"}
    else:
        anf = _anfir_carteira(alvo, list(mercado_total))
        historico = _historico_carteira(alvo, historico_base)
        crm = _crm_carteira(alvo, crm_base)
        registro_alvo = next((item for item in equipe if str(item.get("id")) == str(alvo.id)), {})
        selecao = {
            "modo": "RESPONSAVEL",
            "id": alvo.id,
            "nome": alvo.nome,
            "codigo_regional": registro_alvo.get("codigo_regional"),
            "ddds": registro_alvo.get("ddds") or [],
        }
        escopo = _metadata_escopo(alvo)

    crm_ativos = [item for item in crm if str(item.get("status") or "").upper() not in FECHADOS]
    status_crm = Counter(str(item.get("status") or "SEM_STATUS").upper() for item in crm)
    motivos_perda = Counter(str(item.get("motivo_perda") or "").strip().upper() for item in historico if item.get("motivo_perda"))

    clientes_anfir = _clientes(anf, _nome_cliente_anfir)
    clientes_hist = _clientes(historico, _nome_cliente_historico)
    clientes_crm = _clientes(crm, _nome_cliente_crm)
    universo_clientes = clientes_anfir | clientes_hist | clientes_crm
    anf_hist = clientes_anfir & clientes_hist
    anf_crm = clientes_anfir & clientes_crm
    hist_crm = clientes_hist & clientes_crm
    ponta_a_ponta = clientes_anfir & clientes_hist & clientes_crm

    total_viena = len(mercado_total)
    total_regiao = len(anf)
    percentual_regiao = round((total_regiao / total_viena * 100), 1) if total_viena else 0.0
    sobreposicoes = max(0, soma_individual - total_regiao) if alvo is None else 0

    for item in participacoes_equipe:
        item["participacao_pct"] = round((int(item["mercado"]) / total_viena * 100), 1) if total_viena else 0.0

    return {
        "regra": "ESCOPO_COMERCIAL_CANONICO_SOBRE_MERCADO_REAL_VIENA",
        "metadata": {
            "contexto": contexto_efetivo,
            "periodo": periodo_efetivo,
            "inicio": inicio_efetivo.isoformat(),
            "fim": fim_efetivo.isoformat(),
            "escopo": escopo,
            "fonte_denominador": "MESMA_BASE_DASHBOARD_ANFIR_2026",
            "regra_identidade": "CLIENTE_RECONCILIADO_CTI > RESPONSAVEL_ID_FONTE > RESPONSAVEL_NOME_FONTE",
        },
        "pode_selecionar_responsavel": _pode_gerir(usuario),
        "equipe": [
            {
                "id": item.get("id"),
                "nome": item.get("nome"),
                "tipo_usuario": item.get("tipo_usuario"),
                "codigo_regional": item.get("codigo_regional"),
                "ddds": item.get("ddds") or [],
            }
            for item in equipe
        ],
        "selecao": selecao,
        "mercado": {
            "mercado_real_viena_2026": total_viena,
            "mercado_real_selecao_2026": total_regiao,
            "participacao_regiao_no_mercado_real_pct": percentual_regiao,
            "familias": _familias(anf),
            "clientes_unicos": len(clientes_anfir),
            "participacoes_equipe": participacoes_equipe,
            "soma_mercado_individual": soma_individual if alvo is None else total_regiao,
            "sobreposicoes_entre_carteiras": sobreposicoes,
            "mercado_real_sem_carteira": max(0, total_viena - total_regiao),
        },
        "evidencias": {
            "historico_registros_2026": len(historico),
            "historico_unidades_2026": int(sum(int(item.get("quantidade") or 0) for item in historico)),
            "crm_registros": len(crm),
            "crm_ativos": len(crm_ativos),
            "crm_valor_ativo": round(sum(float(item.get("valor_estimado") or 0) for item in crm_ativos), 2),
            "crm_status": _ranking(status_crm),
            "motivos_perda_historico": _ranking(motivos_perda),
        },
        "reconciliacao": {
            "universo_clientes": len(universo_clientes),
            "clientes_anfir": len(clientes_anfir),
            "clientes_historico": len(clientes_hist),
            "clientes_crm": len(clientes_crm),
            "anfir_historico": len(anf_hist),
            "anfir_crm": len(anf_crm),
            "historico_crm": len(hist_crm),
            "nas_tres_fontes": len(ponta_a_ponta),
            "somente_anfir": len(clientes_anfir - clientes_hist - clientes_crm),
            "somente_historico": len(clientes_hist - clientes_anfir - clientes_crm),
            "somente_crm": len(clientes_crm - clientes_anfir - clientes_hist),
            "historico_fora_mercado_real": len(clientes_hist - clientes_anfir),
            "crm_fora_mercado_real": len(clientes_crm - clientes_anfir),
            "regra": "MESMO_CLIENTE_MESMO_RESPONSAVEL_MESMO_RECORTE; FONTES SAO EVIDENCIAS DIFERENTES",
        },
        "ciclo": {
            "clientes_mercado_real": len(clientes_anfir),
            "clientes_historico_2026": len(clientes_hist),
            "clientes_crm": len(clientes_crm),
            "crm_com_evidencia_historico": len(hist_crm),
            "crm_com_evidencia_anfir": len(anf_crm),
            "clientes_com_evidencia_nas_tres_fontes": len(ponta_a_ponta),
            "nota": "As três fontes usam a mesma carteira canônica. A conciliação separa o mesmo universo de clientes do número de eventos registrados em cada fonte.",
        },
    }
