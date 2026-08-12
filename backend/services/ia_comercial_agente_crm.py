from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from services import ia_comercial_agente as base


_DOMINIOS_CRM = {"propostas", "pedidos", "atividades"}
_EVIDENCIAS_CTI_SEMANTICAS = {"implementadoras_cti"}
_ORIGINAL_FONTES_REQUERIDAS = base._fontes_requeridas
_ORIGINAL_EVIDENCIAS_PRESENTES = base._evidencias_presentes
_ORIGINAL_INSTRUCAO_FALTANTES = base._instrucao_evidencias_faltantes
_ORIGINAL_INSTRUCAO_SINTESE = base._instrucao_sintese_final
_ORIGINAL_INSTRUCOES_AGENTE = base.INSTRUCOES_AGENTE
_ORIGINAL_FERRAMENTAS_AGENTE = base.ferramentas_agente
_EXECUCAO_WEB_PURA: ContextVar[bool] = ContextVar("ia003_execucao_web_pura", default=False)

_INSTRUCOES_WEB_IA003 = """

WEB NATIVA AUTÔNOMA — IA-003:
- Informação externa que possa ter mudado, especialmente lançamentos, disponibilidade, preços, especificações vigentes, legislação/regulação, notícias, movimentos de fabricantes/concorrentes e fatos atuais de mercado, exige pesquisa web real na mesma execução.
- O usuário não precisa escrever "pesquise na web". Decida pela natureza temporal e externa da informação.
- Nunca apresente conhecimento prévio do modelo como se fosse fato externo atual verificado.
- Quando a web for necessária, a execução só possui evidência web se houver fontes reais com URL capturadas pela ferramenta. Uma tentativa de pesquisa sem fonte recuperada não valida o fato.
- Na resposta, separe semanticamente: (1) fatos externos verificados nas fontes da execução; (2) fatos internos CTI, quando consultados; (3) inferências/recomendações comerciais. Não transforme inferência em fato.
- Uma pergunta externa de mercado permanece WEB pura quando o usuário não pedir cruzamento com dados internos e não mencionar uma entidade canônica do CTI que exija grounding interno. Palavras genéricas como venda, equipamento, cliente, produto, mercado ou impacto comercial não autorizam abrir CRM, catálogo, ANFIR ou vendas internas sem contexto suficiente.
- Dados internos entram quando houver intenção explícita de cruzamento com CTI/CRM/ANFIR, nossos dados, nosso portfólio, nossas vendas, nossos clientes, nossos pedidos ou expressão equivalente, ou quando a própria entidade citada possuir significado canônico no CTI que precise ser preservado.
- Para concorrentes, fabricante externo, produto externo ou mercado, descreva somente o que as fontes sustentam e preserve incertezas/divergências entre fontes.
- Fontes externas contextualizam a decisão comercial; não criam vendas, oportunidades, clientes, frota ou qualquer registro interno do CTI.
"""

_INSTRUCOES_GROUNDING_CTI = """

GROUNDING SEMÂNTICO CTI — REGRA ESTRUTURAL:
- O usuário fala em linguagem comercial natural. Nunca exija vocabulário técnico, palavras-chave especiais, ordem de termos ou formulação artificial para compreender uma pergunta.
- Antes de pesquisar a web, resolva o significado das entidades mencionadas pelo usuário contra a taxonomia e as dimensões canônicas do CTI. A web pode enriquecer fatos externos atuais, mas não pode redefinir uma entidade já existente no CTI.
- Preserve distinções de domínio. Em especial, IMPLEMENTADORA é a entidade/dimensão histórica registrada como implementadora nos dados CTI/ANFIR; FABRICANTE DE EQUIPAMENTO é outra dimensão e representa o fabricante do equipamento de refrigeração. Nunca trate fabricantes de refrigeração como sinônimos de implementadoras.
- Para perguntas sobre maiores, principais, líderes, mais frequentes ou ranking de implementadoras, consulte o universo autorizado do CTI com consultar_territorio_cti e use resumo.ranking_implementadoras / resumo.relacoes_implementadoras como base factual. Se o usuário não informou DDD, UF, cidade, linha ou período, não invente filtros: use o universo-base autorizado e TODO_HISTORICO.
- Quando houver CTI + web na mesma pergunta, os nomes e o ranking interno devem nascer do CTI. A web serve para validar existência atual, situação operacional, porte, presença nacional, dados públicos e outras métricas externas das MESMAS entidades, ou para apresentar comparação externa claramente separada. Não substitua a lista CTI por empresas de outra categoria encontradas na web.
- A palavra "maior" não autoriza inventar uma métrica. Se o CTI sustenta frequência/volume de registros históricos, nomeie essa métrica explicitamente. Se a web sustentar faturamento, produção, participação ou outra métrica nacional, identifique a métrica e sua fonte. Não misture métricas como se fossem equivalentes.
- Se houver variantes de grafia que possam representar a mesma entidade, sinalize a necessidade de consolidação/normalização quando isso afetar ranking; não some variantes por suposição sem regra determinística ou evidência suficiente.
- Uma resposta que ignore evidência CTI obrigatória ou troque a categoria semântica da entidade é inválida, mesmo que as informações web sejam verdadeiras.
"""


def _menciona_implementadora(mensagem: str) -> bool:
    texto = base._normalizar(mensagem)
    return any(
        termo in texto
        for termo in (
            "implementadora",
            "implementadoras",
            "implementador",
            "implementadores",
        )
    )


def _fontes_requeridas_crm(mensagem: str) -> set[str]:
    requeridas = set(_ORIGINAL_FONTES_REQUERIDAS(mensagem))
    texto = base._normalizar(mensagem)

    oportunidade_futura_conceitual = any(
        t in texto
        for t in (
            "oportunidade futura",
            "oportunidades futuras",
            "nova oportunidade",
            "novas oportunidades",
            "oportunidade comercial futura",
            "oportunidades comerciais futuras",
            "oportunidades podem ser consideradas",
            "oportunidade pode ser considerada",
        )
    )
    oportunidade_crm_explicita = any(
        t in texto
        for t in (
            "oportunidade do crm",
            "oportunidades do crm",
            "oportunidade no crm",
            "oportunidades no crm",
            "pipeline",
            "status da oportunidade",
            "estágio da oportunidade",
            "estagio da oportunidade",
            "probabilidade da oportunidade",
            "oportunidade registrada",
            "oportunidades registradas",
            "oportunidade vinculada",
            "oportunidades vinculadas",
            "oportunidade relacionada",
            "oportunidades relacionadas",
            "oportunidade associada",
            "oportunidades associadas",
            "oportunidades abertas",
            "oportunidades ganhas",
            "oportunidades perdidas",
        )
    )
    if oportunidade_futura_conceitual and not oportunidade_crm_explicita:
        requeridas.discard("oportunidades")

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
    if _menciona_implementadora(mensagem):
        requeridas.add("implementadoras_cti")

    return requeridas


def _necessita_web_autonoma(mensagem: str) -> bool:
    texto = base._normalizar(mensagem)
    if not texto:
        return False

    explicita = any(
        termo in texto
        for termo in (
            "web", "pesquise na web", "procure na web", "pesquisa web", "pesquisa na web",
            "fontes externas", "fonte externa", "informações externas", "informacoes externas",
            "notícias", "noticias", "mercado", "tendências", "tendencias", "internet",
            "site oficial", "fonte oficial",
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


def _pede_cruzamento_cti_explicito(mensagem: str) -> bool:
    texto = base._normalizar(mensagem)
    if not texto:
        return False

    if "cti" in texto or "crm" in texto or "anfir" in texto:
        return True

    marcadores_internos = (
        "dados internos", "base interna", "nosso portfólio", "nosso portfolio",
        "nossas vendas", "nossos clientes", "nossos pedidos", "nossas oportunidades", "nossas propostas",
        "nossa carteira", "meus clientes", "minhas vendas", "meus pedidos", "minha carteira",
    )
    verbos_cruzamento = (
        "cruze com", "cruzar com", "compare com", "comparar com", "relacione com", "relacionar com",
        "confronte com", "combine com", "à luz dos nossos", "a luz dos nossos",
    )
    return any(t in texto for t in marcadores_internos) or any(t in texto for t in verbos_cruzamento)


def _adicionar_evidencias_cruzamento_expresso(mensagem: str, requeridas: set[str]) -> set[str]:
    texto = base._normalizar(mensagem)
    resultado = set(requeridas)

    if any(t in texto for t in ("nosso portfólio", "nosso portfolio", "catálogo do cti", "catalogo do cti")):
        resultado.add("produtos")
    if any(t in texto for t in ("nossas vendas", "minhas vendas", "vendas do cti", "vendas no cti", "vendas do crm", "vendas no crm")):
        resultado.add("vendas")
    if any(t in texto for t in ("nossos clientes", "meus clientes", "clientes do cti", "clientes no cti", "clientes do crm", "clientes no crm", "nossa carteira", "minha carteira")):
        resultado.add("clientes")
    if any(t in texto for t in ("nossas oportunidades", "oportunidades do cti", "oportunidades no cti", "oportunidades do crm", "oportunidades no crm", "pipeline")):
        resultado.add("oportunidades")
    if any(t in texto for t in ("nossos pedidos", "meus pedidos", "pedidos do cti", "pedidos no cti", "pedidos do crm", "pedidos no crm")):
        resultado.add("pedidos")
    if any(t in texto for t in ("nossas propostas", "propostas do cti", "propostas no cti", "propostas do crm", "propostas no crm")):
        resultado.add("propostas")
    if "anfir" in texto:
        resultado.add("anfir")
    if _menciona_implementadora(mensagem):
        resultado.add("implementadoras_cti")

    return resultado


def _fontes_requeridas_ia003(mensagem: str) -> set[str]:
    requeridas = _fontes_requeridas_crm(mensagem)
    web_necessaria = _necessita_web_autonoma(mensagem)
    if not web_necessaria:
        return requeridas

    cruzamento_explicito = _pede_cruzamento_cti_explicito(mensagem)
    grounding_cti = bool(requeridas & _EVIDENCIAS_CTI_SEMANTICAS)
    if not cruzamento_explicito and not grounding_cti:
        return {"web"}

    requeridas = _adicionar_evidencias_cruzamento_expresso(mensagem, requeridas)
    requeridas.add("web")
    return requeridas


def _evidencias_presentes_crm(rastreio: list[dict[str, Any]], fontes_web: list[dict[str, str]]) -> set[str]:
    presentes = set(_ORIGINAL_EVIDENCIAS_PRESENTES(rastreio, fontes_web))
    for item in rastreio:
        if item.get("tipo") != "CTI":
            continue
        ferramenta = str(item.get("ferramenta") or "")
        if ferramenta == "consultar_dominio_cti":
            dominio = str((item.get("argumentos") or {}).get("dominio") or "")
            if dominio in _DOMINIOS_CRM:
                presentes.add(dominio)
        if ferramenta in {"consultar_territorio_cti", "consultar_anfir_cti"}:
            presentes.add("implementadoras_cti")
    return presentes


def _instrucao_evidencias_faltantes_crm(faltantes: set[str]) -> str:
    crm = {
        "propostas": "consulte consultar_dominio_cti no domínio propostas e use semantica_proposta e vinculos_resolvidos",
        "pedidos": "consulte consultar_dominio_cti no domínio pedidos e use semantica_ciclo e vinculos_resolvidos",
        "atividades": "consulte consultar_dominio_cti no domínio atividades e use somente os vínculos explícitos retornados",
        "implementadoras_cti": (
            "consulte consultar_territorio_cti usando somente os filtros explicitamente pedidos; "
            "se não houver recorte, use TODO_HISTORICO e filtros nulos, e use resumo.ranking_implementadoras "
            "e resumo.relacoes_implementadoras; não use ranking_fabricantes_equipamento como substituto"
        ),
    }
    extensoes = _DOMINIOS_CRM | _EVIDENCIAS_CTI_SEMANTICAS
    passos_crm = "; ".join(crm[x] for x in sorted(faltantes) if x in crm)
    faltantes_base = set(faltantes) - extensoes
    partes = []
    if faltantes_base:
        partes.append(_ORIGINAL_INSTRUCAO_FALTANTES(faltantes_base))
    if passos_crm:
        partes.append(
            "INSTRUÇÃO INTERNA DE EVIDÊNCIA CTI: ainda não finalize. "
            f"Faltam: {', '.join(sorted(set(faltantes) & extensoes))}. {passos_crm}. "
            "Resolva primeiro a entidade no universo CTI; a web não substitui a evidência interna obrigatória."
        )
    return " ".join(partes)


def _instrucao_sintese_final_crm(evidencias: set[str]) -> str:
    evidencias_base = set(evidencias) - _EVIDENCIAS_CTI_SEMANTICAS
    if not evidencias_base:
        evidencias_base = {"territorio"}
    instrucao = _ORIGINAL_INSTRUCAO_SINTESE(evidencias_base)
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
    if "implementadoras_cti" in evidencias:
        regras.append(
            "IMPLEMENTADORAS: a lista/ranking interno deve vir de resumo.ranking_implementadoras do CTI. "
            "Não substitua implementadoras por fabricantes de equipamento. Se a pergunta pedir 'maiores' sem métrica, "
            "descreva o ranking CTI como frequência/volume de registros históricos. Se houver web, use-a para validar ou "
            "enriquecer as mesmas implementadoras e mantenha separada qualquer métrica externa. Não introduza empresa de "
            "outra categoria como se fosse implementadora CTI."
        )
    if "web" in evidencias:
        regras.append(
            "Para fatos externos atuais, use somente a pesquisa web desta execução. Diferencie explicitamente fatos externos verificados de inferências/recomendações comerciais e não atribua fatos web ao CTI."
        )
    return instrucao + (" REGRAS CRM/WEB/GROUNDING: " + " ".join(regras) if regras else "")


def _ferramentas_agente_ia003() -> list[dict[str, Any]]:
    ferramentas = _ORIGINAL_FERRAMENTAS_AGENTE()
    if _EXECUCAO_WEB_PURA.get():
        return [item for item in ferramentas if item.get("type") == "web_search"]
    return ferramentas


def _aplicar_patch() -> None:
    base._fontes_requeridas = _fontes_requeridas_ia003
    base._evidencias_presentes = _evidencias_presentes_crm
    base._instrucao_evidencias_faltantes = _instrucao_evidencias_faltantes_crm
    base._instrucao_sintese_final = _instrucao_sintese_final_crm
    base.ferramentas_agente = _ferramentas_agente_ia003
    base.INSTRUCOES_AGENTE = _ORIGINAL_INSTRUCOES_AGENTE + _INSTRUCOES_WEB_IA003 + _INSTRUCOES_GROUNDING_CTI


def gerar_resposta_agente(mensagem: str, historico: list[dict[str, str]], usuario_id: str, tipo_usuario: str):
    pergunta_original = base._mensagem_original_para_evidencias(mensagem)
    evidencias_previstas = _fontes_requeridas_ia003(pergunta_original)
    token_web_pura = _EXECUCAO_WEB_PURA.set(evidencias_previstas == {"web"})
    try:
        _aplicar_patch()
        texto, metadados = base.gerar_resposta_agente(mensagem, historico, usuario_id, tipo_usuario)
    finally:
        _EXECUCAO_WEB_PURA.reset(token_web_pura)

    web_requerida = "web" in set(metadados.get("evidencias_requeridas") or [])
    fontes_web = [
        fonte for fonte in (metadados.get("fontes") or [])
        if isinstance(fonte, dict) and fonte.get("url")
    ]
    metadados["controle_web_nativa"] = "ia003_web_autonoma_com_proveniencia"
    metadados["web_requerida"] = web_requerida
    metadados["web_fontes_validas"] = len(fontes_web)
    metadados["web_urls_auditaveis"] = [str(fonte.get("url")) for fonte in fontes_web]
    metadados["controle_cruzamento_web_cti"] = (
        "explicito_usuario" if _pede_cruzamento_cti_explicito(pergunta_original) else "nao_solicitado"
    )
    metadados["controle_grounding_semantico_cti"] = (
        "entidade_cti_ancorada" if evidencias_previstas & _EVIDENCIAS_CTI_SEMANTICAS else "nao_aplicavel"
    )
    metadados["controle_ferramentas_web_pura"] = (
        "somente_web_search" if evidencias_previstas == {"web"} else "catalogo_completo_autorizado"
    )
    if web_requerida and not fontes_web:
        raise base.IAComercialOpenAIError(
            "A IA não conseguiu obter fontes externas verificáveis para responder com segurança.",
            codigo="AGENT_WEB_SOURCE_MISSING",
        )
    return texto, metadados