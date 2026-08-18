from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from services import ia_comercial_agente as base
from services.ia_comercial_universo import catalogar_universo_cti, consultar_universo_cti


# Contratos históricos de fase mantidos apenas como nomes de API interna; a execução é universal e canônica.
# Estes nomes permanecem estáveis para as camadas posteriores, mas a execução
# efetiva é substituída abaixo pela arquitetura universal de leitura.
_DOMINIOS_CRM = {"propostas", "pedidos", "atividades"}
_ORIGINAL_FONTES_REQUERIDAS = base._fontes_requeridas
_ORIGINAL_EVIDENCIAS_PRESENTES = base._evidencias_presentes
_ORIGINAL_INSTRUCAO_FALTANTES = base._instrucao_evidencias_faltantes
_ORIGINAL_INSTRUCAO_SINTESE = base._instrucao_sintese_final
_ORIGINAL_INSTRUCOES_AGENTE = base.INSTRUCOES_AGENTE
_ORIGINAL_FERRAMENTAS_AGENTE = base.ferramentas_agente
_ORIGINAL_EXECUTOR = base._executar_ferramenta_cti
_EXECUCAO_WEB_PURA: ContextVar[bool] = ContextVar("ia_universal_execucao_web_pura", default=False)


_INSTRUCOES_UNIVERSAIS = """

ARQUITETURA UNIVERSAL DE LEITURA CTI — REGRA OBRIGATÓRIA:
- O usuário fala em linguagem natural livre. Nunca exija palavras-chave, comandos especiais, nomes de tabelas, nomes de campos ou conhecimento da arquitetura do CTI.
- Para responder sobre a operação, descubra autonomamente quais dados internos são necessários. Você dispõe de um catálogo do universo autorizado e de uma consulta universal somente leitura.
- Não existe uma ferramenta diferente para cada palavra ou entidade. Use catalogar_universo_cti para descobrir fontes/campos quando necessário e consultar_universo_cti para executar filtros, agrupamentos, métricas, ordenações e paginação.
- O nome da fonte é detalhe interno. Na resposta ao usuário, fale em termos comerciais, não em nomes técnicos de tabela ou função.
- O banco pode crescer. Não presuma que o conjunto de campos de uma fonte é fixo; o catálogo devolve os campos efetivamente disponíveis na execução.
- Para perguntas factuais sobre dados internos, consultar o catálogo sozinho NÃO basta: execute pelo menos uma consulta universal sobre a fonte apropriada antes de responder.
- Quando a pergunta envolver mais de um conceito, você pode consultar várias fontes e cruzar os resultados. Use campos relacionais reais quando existirem; não invente vínculos.
- Quando houver necessidade de comparar, ranquear ou responder "maiores", "menores", "mais frequentes", "melhores" ou equivalentes, identifique a métrica disponível nos dados e calcule-a com agrupamento/métrica. Não invente o critério.
- IMPLEMENTADORA e FABRICANTE DE EQUIPAMENTO são conceitos distintos. Essa distinção decorre dos próprios campos/dados do CTI; não substitua um pelo outro por associação linguística ou por resultados da web.
- A fonte historico_anfir contém o histórico autorizado e pode ser agrupada por qualquer campo disponível, inclusive implementadora, cliente, DDD, estado, linha, modelo, fabricante_equipamento, fabricante_caminhao e demais dimensões existentes.
- A fonte implementadoras_cadastro é o cadastro canônico atual de implementadoras. O histórico e o cadastro têm funções diferentes e podem ser cruzados quando pertinente.
- A fonte perfil_usuario contém somente o perfil operacional autorizado do usuário atual e pode ser usada para contextualizar escopo, linguagem e recomendações quando necessário.

WEB E PROVENIÊNCIA:
- Para fatos externos atuais, use web_search real na mesma execução.
- A web complementa o CTI; não redefine entidades internas nem substitui dados internos pedidos pelo usuário.
- Quando houver CTI + web, primeiro estabeleça o que os dados internos mostram e depois use a web para validar/enriquecer/comparar. Separe claramente as métricas e proveniências.
- Nunca apresente conhecimento prévio do modelo como fato externo atual verificado.

SEGURANÇA:
- A leitura universal NÃO é SQL livre. Você não recebe terminal, schema administrativo, credenciais, GitHub, Vercel, Render ou acesso de escrita.
- Toda consulta universal é validada pelo backend contra fontes autorizadas e RBAC antes da execução.
- Escritas continuam exclusivamente pelo fluxo de ações controladas com autorização, confirmação e auditoria; não tente escrever por esta camada.
"""


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _somente_web_explicito(mensagem: str) -> bool:
    texto = _normalizar(mensagem)
    return any(
        termo in texto
        for termo in (
            "somente na web",
            "somente web",
            "apenas na web",
            "apenas web",
            "não use o cti",
            "nao use o cti",
            "sem usar o cti",
        )
    )


def _necessita_web(mensagem: str) -> bool:
    texto = _normalizar(mensagem)
    if not texto:
        return False
    if _somente_web_explicito(mensagem):
        return True

    marcadores_externos_ou_temporais = (
        "web", "internet", "pesquise", "pesquisa", "procure", "mercado", "mercado atual",
        "atualmente", "hoje", "recente", "recentes", "mais recente", "mais recentes",
        "novidade", "novidades", "notícia", "noticia", "notícias", "noticias",
        "fonte externa", "fontes externas", "site oficial", "vigente", "vigentes",
        "lançamento", "lancamento", "lançamentos", "lancamentos", "preço atual", "preco atual",
    )
    return any(termo in texto for termo in marcadores_externos_ou_temporais)


def _fontes_requeridas_universais(mensagem: str) -> set[str]:
    if _somente_web_explicito(mensagem):
        return {"web"}
    requeridas = {"universo_cti"}
    if _necessita_web(mensagem):
        requeridas.add("web")
    return requeridas


# Contratos semânticos de fase preservados para planejamento/auditoria.
# Eles não escolhem as ferramentas da execução universal; servem apenas como
# API estável para as camadas antigas e seus testes de semântica operacional.
def _fontes_requeridas_crm(mensagem: str) -> set[str]:
    requeridas = set(_ORIGINAL_FONTES_REQUERIDAS(mensagem))
    texto = base._normalizar(mensagem)

    oportunidade_futura_conceitual = any(
        t in texto
        for t in (
            "oportunidade futura", "oportunidades futuras", "nova oportunidade", "novas oportunidades",
            "oportunidade comercial futura", "oportunidades comerciais futuras",
            "oportunidades podem ser consideradas", "oportunidade pode ser considerada",
        )
    )
    oportunidade_crm_explicita = any(
        t in texto
        for t in (
            "oportunidade do crm", "oportunidades do crm", "oportunidade no crm", "oportunidades no crm",
            "pipeline", "status da oportunidade", "estágio da oportunidade", "estagio da oportunidade",
            "probabilidade da oportunidade", "oportunidade registrada", "oportunidades registradas",
            "oportunidade vinculada", "oportunidades vinculadas", "oportunidade relacionada",
            "oportunidades relacionadas", "oportunidade associada", "oportunidades associadas",
            "oportunidades abertas", "oportunidades ganhas", "oportunidades perdidas",
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
    return requeridas


def _evidencias_presentes_crm(rastreio: list[dict[str, Any]], fontes_web: list[dict[str, str]]) -> set[str]:
    presentes = set(_ORIGINAL_EVIDENCIAS_PRESENTES(rastreio, fontes_web))
    for item in rastreio:
        if item.get("tipo") != "CTI":
            continue
        if str(item.get("ferramenta") or "") != "consultar_dominio_cti":
            continue
        dominio = str((item.get("argumentos") or {}).get("dominio") or "")
        if dominio in _DOMINIOS_CRM:
            presentes.add(dominio)
    return presentes


# Aliases de fase preservados somente para compatibilidade de testes e contratos internos.
# As camadas antigas podem continuar importando estes nomes sem controlar
# o roteamento real, que permanece universal.
def _fontes_requeridas_ia003(mensagem: str) -> set[str]:
    return _fontes_requeridas_universais(mensagem)


def _necessita_web_autonoma(mensagem: str) -> bool:
    return _necessita_web(mensagem)


def _pede_cruzamento_cti_explicito(mensagem: str) -> bool:
    return not _somente_web_explicito(mensagem)


def _evidencias_presentes_universais(rastreio: list[dict[str, Any]], fontes_web: list[dict[str, str]]) -> set[str]:
    presentes: set[str] = set()
    if fontes_web:
        presentes.add("web")
    for item in rastreio:
        if item.get("tipo") != "CTI":
            continue
        ferramenta = str(item.get("ferramenta") or "")
        if ferramenta == "catalogar_universo_cti":
            presentes.add("catalogo_cti")
        elif ferramenta == "consultar_universo_cti" and not (item.get("resumo") or {}).get("erro"):
            presentes.add("universo_cti")
    return presentes


def _instrucao_evidencias_faltantes_universal(faltantes: set[str]) -> str:
    passos: list[str] = []
    if "universo_cti" in faltantes:
        passos.append(
            "execute consultar_universo_cti sobre a fonte apropriada; se ainda não souber a fonte/campos, "
            "consulte catalogar_universo_cti uma vez e em seguida execute consultar_universo_cti"
        )
    if "web" in faltantes:
        passos.append("execute web_search real e obtenha fontes URL verificáveis")
    return (
        "INSTRUÇÃO INTERNA DE EVIDÊNCIA: ainda não finalize. "
        f"Faltam: {', '.join(sorted(faltantes))}. {'; '.join(passos)}. "
        "Não repita a mesma consulta sem alterar o plano. O histórico da conversa não substitui evidência desta execução."
    )


def _instrucao_sintese_final_universal(evidencias: set[str]) -> str:
    regras = [
        "INSTRUÇÃO INTERNA DE SÍNTESE FINAL: as evidências exigidas já foram coletadas. Não faça novas consultas.",
        "Responda à pergunta original usando concretamente os resultados das consultas universais desta execução.",
        "Diferencie fatos internos CTI, fatos externos verificados e inferências/recomendações.",
        "Não exponha nomes de ferramentas, tabelas ou detalhes de function calling ao usuário.",
        "Não invente vínculos, métricas, números, status ou entidades ausentes dos resultados.",
    ]
    if "web" in evidencias:
        regras.append("A web é complemento: preserve a identidade e as métricas internas do CTI e deixe separada qualquer métrica externa.")
    return " ".join(regras)


def _schema_filtro() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "campo": {"type": "string"},
            "operador": {"type": "string", "enum": ["eq", "neq", "contains", "in", "gt", "gte", "lt", "lte", "is_null", "not_null"]},
            "valor": {"type": ["string", "null"]},
            "valores": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["campo", "operador", "valor", "valores"],
        "additionalProperties": False,
    }


def _schema_metrica() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "operacao": {"type": "string", "enum": ["count", "sum", "avg", "min", "max"]},
            "campo": {"type": ["string", "null"]},
            "alias": {"type": "string"},
        },
        "required": ["operacao", "campo", "alias"],
        "additionalProperties": False,
    }


def _ferramentas_universais() -> list[dict[str, Any]]:
    if _EXECUCAO_WEB_PURA.get():
        return [
            {"type": "web_search", "search_context_size": "high", "user_location": {"type": "approximate", "country": "BR", "region": "São Paulo", "city": "São Paulo", "timezone": "America/Sao_Paulo"}}
        ]
    return [
        {"type": "web_search", "search_context_size": "high", "user_location": {"type": "approximate", "country": "BR", "region": "São Paulo", "city": "São Paulo", "timezone": "America/Sao_Paulo"}},
        {"type": "code_interpreter", "container": {"type": "auto"}},
        {
            "type": "function",
            "name": "catalogar_universo_cti",
            "description": "Descobre dinamicamente as fontes e campos do universo de dados CTI que o usuário atual pode consultar. Use quando precisar entender onde está um dado ou quais campos existem.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            "strict": True,
        },
        {
            "type": "function",
            "name": "consultar_universo_cti",
            "description": "Executa uma consulta somente leitura sobre qualquer fonte autorizada do catálogo CTI, com filtros, busca textual, agrupamentos, métricas, ordenação e paginação. Use linguagem natural para raciocinar e transforme a necessidade em plano estruturado; não há SQL livre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fonte": {"type": "string"},
                    "filtros": {"type": "array", "items": _schema_filtro()},
                    "termo": {"type": ["string", "null"]},
                    "agrupar_por": {"type": "array", "items": {"type": "string"}},
                    "metricas": {"type": "array", "items": _schema_metrica()},
                    "ordenar_por": {"type": ["string", "null"]},
                    "direcao": {"type": "string", "enum": ["asc", "desc"]},
                    "limite": {"type": "integer", "minimum": 1, "maximum": 200},
                    "offset": {"type": "integer", "minimum": 0},
                },
                "required": ["fonte", "filtros", "termo", "agrupar_por", "metricas", "ordenar_por", "direcao", "limite", "offset"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]


def _executar_ferramenta_universal(nome: str, argumentos: dict[str, Any], usuario_id: str, tipo_usuario: str) -> dict[str, Any]:
    if nome == "catalogar_universo_cti":
        return {"ferramenta": nome, **catalogar_universo_cti(usuario_id, tipo_usuario)}
    if nome == "consultar_universo_cti":
        filtros = []
        for item in argumentos.get("filtros") or []:
            if not isinstance(item, dict):
                continue
            filtro = dict(item)
            if str(filtro.get("operador") or "") == "in":
                filtro["valor"] = filtro.get("valores") or []
            filtro.pop("valores", None)
            filtros.append(filtro)
        resultado = consultar_universo_cti(
            usuario_id,
            tipo_usuario,
            fonte=str(argumentos.get("fonte") or ""),
            filtros=filtros,
            termo=argumentos.get("termo"),
            agrupar_por=argumentos.get("agrupar_por") or [],
            metricas=argumentos.get("metricas") or [],
            ordenar_por=argumentos.get("ordenar_por"),
            direcao=str(argumentos.get("direcao") or "desc"),
            limite=int(argumentos.get("limite") or 50),
            offset=int(argumentos.get("offset") or 0),
        )
        return {"ferramenta": nome, **resultado}
    return _ORIGINAL_EXECUTOR(nome, argumentos, usuario_id, tipo_usuario)


def _aplicar_patch() -> None:
    base._fontes_requeridas = _fontes_requeridas_universais
    base._evidencias_presentes = _evidencias_presentes_universais
    base._instrucao_evidencias_faltantes = _instrucao_evidencias_faltantes_universal
    base._instrucao_sintese_final = _instrucao_sintese_final_universal
    base.ferramentas_agente = _ferramentas_universais
    base._executar_ferramenta_cti = _executar_ferramenta_universal
    base.INSTRUCOES_AGENTE = _ORIGINAL_INSTRUCOES_AGENTE + _INSTRUCOES_UNIVERSAIS


def gerar_resposta_agente(mensagem: str, historico: list[dict[str, str]], usuario_id: str, tipo_usuario: str):
    pergunta_original = base._mensagem_original_para_evidencias(mensagem)
    evidencias_previstas = _fontes_requeridas_universais(pergunta_original)
    token_web_pura = _EXECUCAO_WEB_PURA.set(evidencias_previstas == {"web"})
    try:
        _aplicar_patch()
        texto, metadados = base.gerar_resposta_agente(mensagem, historico, usuario_id, tipo_usuario)
    finally:
        _EXECUCAO_WEB_PURA.reset(token_web_pura)

    fontes_web = [
        fonte for fonte in (metadados.get("fontes") or [])
        if isinstance(fonte, dict) and fonte.get("url")
    ]
    metadados["arquitetura_leitura"] = "universo_cti_semantico_read_only"
    metadados["controle_roteamento"] = "modelo_decide_plano_sem_palavras_chave_de_dominio"
    metadados["controle_sql"] = "sql_livre_indisponivel"
    metadados["controle_rbac_universal"] = "backend"
    metadados["web_requerida"] = "web" in evidencias_previstas
    metadados["web_fontes_validas"] = len(fontes_web)
    metadados["web_urls_auditaveis"] = [str(fonte.get("url")) for fonte in fontes_web]
    metadados["controle_ferramentas_web_pura"] = "somente_web_search" if evidencias_previstas == {"web"} else "universo_cti_mais_web"

    if "web" in evidencias_previstas and not fontes_web:
        raise base.IAComercialOpenAIError(
            "A IA não conseguiu obter fontes externas verificáveis para responder com segurança.",
            codigo="AGENT_WEB_SOURCE_MISSING",
        )
    return texto, metadados