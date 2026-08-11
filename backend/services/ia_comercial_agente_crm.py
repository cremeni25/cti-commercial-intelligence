from __future__ import annotations

from typing import Any

from services import ia_comercial_agente as base


_DOMINIOS_CRM = {"propostas", "pedidos", "atividades"}
_ORIGINAL_FONTES_REQUERIDAS = base._fontes_requeridas
_ORIGINAL_EVIDENCIAS_PRESENTES = base._evidencias_presentes
_ORIGINAL_INSTRUCAO_FALTANTES = base._instrucao_evidencias_faltantes
_ORIGINAL_INSTRUCAO_SINTESE = base._instrucao_sintese_final


def _fontes_requeridas_crm(mensagem: str) -> set[str]:
    requeridas = set(_ORIGINAL_FONTES_REQUERIDAS(mensagem))
    texto = base._normalizar(mensagem)

    if any(t in texto for t in ("proposta", "propostas", "aceite", "aceita", "aceito", "recusada", "recusado")):
        requeridas.add("propostas")
    if any(
        t in texto
        for t in (
            "pedido", "pedidos", "acompanhamento", "ciclo operacional", "carrier", "faturado",
            "faturamento", "entregue", "entrega", "instalado", "instalação", "instalacao", "encerrado",
            "número da nf", "numero da nf", "número de série", "numero de serie",
        )
    ):
        requeridas.add("pedidos")
    if any(t in texto for t in ("atividade", "atividades", "visita", "visitas", "agenda", "última interação", "ultima interacao")):
        requeridas.add("atividades")

    return requeridas


def _evidencias_presentes_crm(rastreio: list[dict[str, Any]], fontes_web: list[dict[str, str]]) -> set[str]:
    presentes = set(_ORIGINAL_EVIDENCIAS_PRESENTES(rastreio, fontes_web))
    for item in rastreio:
        if item.get("tipo") != "CTI" or item.get("ferramenta") != "consultar_dominio_cti":
            continue
        dominio = str((item.get("argumentos") or {}).get("dominio") or "")
        if dominio in _DOMINIOS_CRM:
            presentes.add(dominio)
    return presentes


def _instrucao_evidencias_faltantes_crm(faltantes: set[str]) -> str:
    crm = {
        "propostas": "consulte consultar_dominio_cti no domínio propostas e use semantica_proposta e vinculos_resolvidos",
        "pedidos": "consulte consultar_dominio_cti no domínio pedidos e use semantica_ciclo e vinculos_resolvidos",
        "atividades": "consulte consultar_dominio_cti no domínio atividades e use somente os vínculos explícitos retornados",
    }
    passos_crm = "; ".join(crm[x] for x in sorted(faltantes) if x in crm)
    faltantes_base = set(faltantes) - _DOMINIOS_CRM
    partes = []
    if faltantes_base:
        partes.append(_ORIGINAL_INSTRUCAO_FALTANTES(faltantes_base))
    if passos_crm:
        partes.append(
            "INSTRUÇÃO INTERNA DE EVIDÊNCIA CRM: ainda não finalize. "
            f"Faltam: {', '.join(sorted(set(faltantes) & _DOMINIOS_CRM))}. {passos_crm}. "
            "O CRM já possui esses controles; consulte-os como fonte factual sem recriar regras paralelas."
        )
    return " ".join(partes)


def _instrucao_sintese_final_crm(evidencias: set[str]) -> str:
    instrucao = _ORIGINAL_INSTRUCAO_SINTESE(evidencias)
    regras = []
    if "propostas" in evidencias:
        regras.append(
            "Para propostas/aceites, use semantica_proposta e vinculos_resolvidos; não deduza aceite ou recusa apenas do texto, e não diga que há pedido sem vínculo explícito."
        )
    if "pedidos" in evidencias:
        regras.append(
            "Para pedidos, use semantica_ciclo como verdade operacional: PEDIDO → CARRIER → FATURADO → ENTREGUE → INSTALADO → ENCERRADO. Informe etapa atual, próxima etapa, pendências e inconsistências exatamente como retornadas; não salte etapas."
        )
    if "atividades" in evidencias:
        regras.append(
            "Para atividades/visitas, use apenas cliente e oportunidade presentes em vinculos_resolvidos; ausência de atividade registrada não prova ausência de contato no mundo real."
        )
    return instrucao + (" REGRAS CRM OPERACIONAL: " + " ".join(regras) if regras else "")


def _aplicar_patch() -> None:
    base._fontes_requeridas = _fontes_requeridas_crm
    base._evidencias_presentes = _evidencias_presentes_crm
    base._instrucao_evidencias_faltantes = _instrucao_evidencias_faltantes_crm
    base._instrucao_sintese_final = _instrucao_sintese_final_crm


def gerar_resposta_agente(mensagem: str, historico: list[dict[str, str]], usuario_id: str, tipo_usuario: str):
    _aplicar_patch()
    return base.gerar_resposta_agente(mensagem, historico, usuario_id, tipo_usuario)
