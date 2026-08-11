from __future__ import annotations

from typing import Any

from services import ia_comercial_agente as base


_DOMINIOS_CRM = {"propostas", "pedidos", "atividades"}
_ORIGINAL_FONTES_REQUERIDAS = base._fontes_requeridas
_ORIGINAL_EVIDENCIAS_PRESENTES = base._evidencias_presentes
_ORIGINAL_INSTRUCAO_FALTANTES = base._instrucao_evidencias_faltantes
_ORIGINAL_INSTRUCAO_SINTESE = base._instrucao_sintese_final
_ORIGINAL_INSTRUCOES_AGENTE = base.INSTRUCOES_AGENTE

_INSTRUCOES_WEB_IA003 = """

WEB NATIVA AUTÔNOMA — IA-003:
- Informação externa que possa ter mudado, especialmente lançamentos, disponibilidade, preços, especificações vigentes, legislação/regulação, notícias, movimentos de fabricantes/concorrentes e fatos atuais de mercado, exige pesquisa web real na mesma execução.
- O usuário não precisa escrever "pesquise na web". Decida pela natureza temporal e externa da informação.
- Nunca apresente conhecimento prévio do modelo como se fosse fato externo atual verificado.
- Quando a web for necessária, a execução só possui evidência web se houver fontes reais com URL capturadas pela ferramenta. Uma tentativa de pesquisa sem fonte recuperada não valida o fato.
- Na resposta, separe semanticamente: (1) fatos externos verificados nas fontes da execução; (2) fatos internos CTI, quando consultados; (3) inferências/recomendações comerciais. Não transforme inferência em fato.
- Para concorrentes, fabricante externo, produto externo ou mercado, descreva somente o que as fontes sustentam e preserve incertezas/divergências entre fontes.
- Fontes externas contextualizam a decisão comercial; não criam vendas, oportunidades, clientes, frota ou qualquer registro interno do CTI.
"""


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


def _necessita_web_autonoma(mensagem: str) -> bool:
    texto = base._normalizar(mensagem)
    if not texto:
        return False

    explicita = any(
        termo in texto
        for termo in (
            "pesquise na web", "procure na web", "pesquisa web", "fontes externas", "fonte externa",
            "informações externas", "informacoes externas", "notícias", "noticias", "mercado",
            "tendências", "tendencias", "internet", "site oficial", "fonte oficial",
        )
    )
    if explicita:
        return True

    atualidade = any(
        termo in texto
        for termo in (
            "atualmente", "atual", "mais recente", "mais recentes", "recentemente", "hoje",
            "últimas", "ultimas", "últimos", "ultimos", "novidade", "novidades", "lançamento",
            "lancamento", "lançamentos", "lancamentos", "disponível agora", "disponivel agora",
            "vigente", "vigentes", "em 2026",
        )
    )
    externo_comercial = any(
        termo in texto
        for termo in (
            "thermo king", "thermoking", "frigoking", "thermostar", "thermoflex", "rodofrio",
            "palácio", "palacio", "concorrente", "concorrentes", "fabricante", "fabricantes",
            "produto concorrente", "equipamento concorrente", "preço", "preco", "regulação",
            "regulacao", "legislação", "legislacao", "norma", "normas", "governo", "anfavea",
            "anfir nacional", "transportes frigorificados", "refrigeração de transporte",
            "refrigeracao de transporte",
        )
    )
    return atualidade and externo_comercial


def _fontes_requeridas_ia003(mensagem: str) -> set[str]:
    requeridas = _fontes_requeridas_crm(mensagem)
    if _necessita_web_autonoma(mensagem):
        requeridas.add("web")
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
    if "web" in evidencias:
        regras.append(
            "Para fatos externos atuais, use somente a pesquisa web desta execução. Diferencie explicitamente fatos externos verificados de inferências/recomendações comerciais e não atribua fatos web ao CTI."
        )
    return instrucao + (" REGRAS CRM/WEB: " + " ".join(regras) if regras else "")


def _aplicar_patch() -> None:
    base._fontes_requeridas = _fontes_requeridas_ia003
    base._evidencias_presentes = _evidencias_presentes_crm
    base._instrucao_evidencias_faltantes = _instrucao_evidencias_faltantes_crm
    base._instrucao_sintese_final = _instrucao_sintese_final_crm
    base.INSTRUCOES_AGENTE = _ORIGINAL_INSTRUCOES_AGENTE + _INSTRUCOES_WEB_IA003


def gerar_resposta_agente(mensagem: str, historico: list[dict[str, str]], usuario_id: str, tipo_usuario: str):
    _aplicar_patch()
    texto, metadados = base.gerar_resposta_agente(mensagem, historico, usuario_id, tipo_usuario)
    web_requerida = "web" in set(metadados.get("evidencias_requeridas") or [])
    fontes_web = [
        fonte for fonte in (metadados.get("fontes") or [])
        if isinstance(fonte, dict) and fonte.get("url")
    ]
    metadados["controle_web_nativa"] = "ia003_web_autonoma_com_proveniencia"
    metadados["web_requerida"] = web_requerida
    metadados["web_fontes_validas"] = len(fontes_web)
    metadados["web_urls_auditaveis"] = [str(fonte.get("url")) for fonte in fontes_web]
    if web_requerida and not fontes_web:
        raise base.IAComercialOpenAIError(
            "A IA não conseguiu obter fontes externas verificáveis para responder com segurança.",
            codigo="AGENT_WEB_SOURCE_MISSING",
        )
    return texto, metadados
