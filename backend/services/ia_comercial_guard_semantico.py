from __future__ import annotations

from typing import Any

from services import ia_comercial_agente as base
from services import ia_comercial_agente_crm as crm


_ORIGINAL_GERAR = crm.gerar_resposta_agente


_RANKING_INTENT = (
    "maior", "maiores", "menor", "menores", "ranking", "top ", "líder", "lider", "líderes", "lideres",
    "mais frequente", "mais frequentes", "mais relevante", "mais relevantes",
)

_CONTEXTOS_WEB_INVALIDOS_IMPLEMENTADORA = (
    " sap ", "sap-", "/sap", "oracle", "servicenow", "service now", "erp", "core banking",
    "integradora de sistemas", "consultoria de tecnologia", "software empresarial",
)

_CONTEXTOS_WEB_VALIDOS_IMPLEMENTADORA = (
    "implemento rodovi", "implementos rodovi", "carroceria", "carrocerias", "semirreboque",
    "semirreboques", "reboque", "reboques", "baú", "bau", "transporte rodovi",
)


def _normalizar(valor: Any) -> str:
    return " " + str(valor or "").strip().casefold() + " "


def _rastreio_cti(metadados: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in (metadados.get("ferramentas") or [])
        if isinstance(item, dict) and item.get("tipo") == "CTI"
    ]


def _args(item: dict[str, Any]) -> dict[str, Any]:
    argumentos = item.get("argumentos") or {}
    return argumentos if isinstance(argumentos, dict) else {}


def _dominio_implementadora_fixado(metadados: dict[str, Any]) -> bool:
    for item in _rastreio_cti(metadados):
        argumentos = _args(item)
        if str(argumentos.get("fonte") or "") == "implementadoras_cadastro":
            return True
        if "implementadora" in {str(campo) for campo in (argumentos.get("agrupar_por") or [])}:
            return True
        for filtro in argumentos.get("filtros") or []:
            if isinstance(filtro, dict) and str(filtro.get("campo") or "") == "implementadora":
                return True
    return False


def _usou_historico_implementadora(metadados: dict[str, Any]) -> bool:
    for item in _rastreio_cti(metadados):
        argumentos = _args(item)
        if str(argumentos.get("fonte") or "") != "historico_anfir":
            continue
        if "implementadora" in {str(campo) for campo in (argumentos.get("agrupar_por") or [])}:
            return True
        for filtro in argumentos.get("filtros") or []:
            if isinstance(filtro, dict) and str(filtro.get("campo") or "") == "implementadora":
                return True
    return False


def _ranking_solicitado(mensagem: str) -> bool:
    texto = _normalizar(mensagem)
    return any(marcador in texto for marcador in _RANKING_INTENT)


def _texto_fontes_web(metadados: dict[str, Any]) -> str:
    partes: list[str] = []
    for fonte in metadados.get("fontes") or []:
        if not isinstance(fonte, dict) or not fonte.get("url"):
            continue
        partes.extend([str(fonte.get("descricao") or ""), str(fonte.get("url") or "")])
    return _normalizar(" ".join(partes))


def _web_derivou_para_outro_setor(metadados: dict[str, Any]) -> bool:
    if not _dominio_implementadora_fixado(metadados):
        return False
    texto = _texto_fontes_web(metadados)
    if not texto.strip():
        return False
    invalidos = any(marcador in texto for marcador in _CONTEXTOS_WEB_INVALIDOS_IMPLEMENTADORA)
    validos = any(marcador in texto for marcador in _CONTEXTOS_WEB_VALIDOS_IMPLEMENTADORA)
    return invalidos and not validos


def _motivos_deriva(mensagem: str, metadados: dict[str, Any]) -> list[str]:
    motivos: list[str] = []
    if _dominio_implementadora_fixado(metadados):
        if _ranking_solicitado(mensagem) and not _usou_historico_implementadora(metadados):
            motivos.append("ranking_de_implementadora_sem_fonte_historica")
        if _web_derivou_para_outro_setor(metadados):
            motivos.append("web_fora_da_ontologia_de_implementadora")
    return motivos


def _mensagem_retry(mensagem: str, motivos: list[str]) -> str:
    return (
        mensagem
        + "\n\nINSTRUÇÃO INTERNA DE RETENTATIVA SEMÂNTICA — NÃO EXIBIR AO USUÁRIO: "
        + "A execução anterior foi rejeitada pelo guard de ontologia ("
        + ", ".join(motivos)
        + "). Preserve a pergunta original. Consulte primeiro catalogar_universo_cti. "
        + "Fixe a entidade e o setor pela ontologia CTI. Para ranking/frequência de implementadoras, "
        + "não use o cadastro como métrica: use a fonte analítica histórica compatível e agrupe pelo campo real. "
        + "Na web, mantenha o mesmo setor de implementos rodoviários/carrocerias/baús/semirreboques; "
        + "descarte SAP, Oracle, ServiceNow, ERP, core banking e consultorias de TI. "
        + "Separe a métrica interna da métrica externa e só finalize com fontes semanticamente compatíveis."
    )


def gerar_resposta_agente(
    mensagem: str,
    historico: list[dict[str, str]],
    usuario_id: str,
    tipo_usuario: str,
):
    texto, metadados = _ORIGINAL_GERAR(mensagem, historico, usuario_id, tipo_usuario)
    motivos = _motivos_deriva(mensagem, metadados)
    if not motivos:
        metadados["controle_estabilidade_ontologica"] = "aprovado_primeira_execucao"
        return texto, metadados

    texto_retry, metadados_retry = _ORIGINAL_GERAR(
        _mensagem_retry(mensagem, motivos),
        historico,
        usuario_id,
        tipo_usuario,
    )
    motivos_retry = _motivos_deriva(mensagem, metadados_retry)
    if motivos_retry:
        raise base.IAComercialOpenAIError(
            "A IA bloqueou uma resposta cuja investigação desviou do significado comercial dos dados CTI.",
            codigo="AGENT_SEMANTIC_DRIFT_BLOCKED",
        )

    metadados_retry["controle_estabilidade_ontologica"] = "corrigido_por_retry_automatico"
    metadados_retry["deriva_semantica_bloqueada"] = motivos
    return texto_retry, metadados_retry


def aplicar_patch_guard() -> None:
    crm.gerar_resposta_agente = gerar_resposta_agente


aplicar_patch_guard()
