from __future__ import annotations

import re
from contextvars import ContextVar
from copy import deepcopy
from typing import Any

from services import ia_comercial_agente as base
from services import ia_comercial_agente_crm as crm
from services.ia_comercial_sintese_factual import sintetizar_fatos_execucao as sintetizar_fatos_base


EVIDENCIAS_CRM = {"propostas", "pedidos", "atividades"}
_DOMINIOS_CTI = {"clientes", "oportunidades", "itens", "propostas", "pedidos", "atividades", "vendas"}
_EVIDENCIAS_IA004: ContextVar[frozenset[str]] = ContextVar("ia004_evidencias", default=frozenset())
_PERGUNTA_IA004: ContextVar[str] = ContextVar("ia004_pergunta", default="")

_ORIGINAL_FONTES_IA003 = crm._fontes_requeridas_ia003
_ORIGINAL_FERRAMENTAS_CRM = crm._ORIGINAL_FERRAMENTAS_AGENTE
_ORIGINAL_INSTRUCOES_CRM = crm._ORIGINAL_INSTRUCOES_AGENTE
_ORIGINAL_INSTRUCAO_SINTESE_CRM = crm._ORIGINAL_INSTRUCAO_SINTESE
_ORIGINAL_GERAR_BASE = base.gerar_resposta_agente
_ORIGINAL_EXECUTAR_FERRAMENTA = base._executar_ferramenta_cti

_INSTRUCOES_IA004 = """

CRUZAMENTO MULTI-FONTE — IA-004:
- Quando a pergunta exigir simultaneamente WEB e dados internos CTI, trate cada origem como evidência independente.
- Fato externo só pode ser sustentado pelas fontes web da execução. Fato interno só pode ser sustentado pelas ferramentas CTI efetivamente consultadas.
- Uma fonte nunca completa, confirma ou substitui silenciosamente a outra: web não cria venda, cliente, oportunidade, pedido, frota ou registro CTI; CTI não prova tendência, participação ou fato do mercado externo.
- Ausência significa somente ausência na fonte, domínio, filtro e recorte consultados. Nunca converta resultado interno vazio em ausência no mercado real, nem ausência web em ausência no CTI.
- Pedido por "nosso portfólio" significa o catálogo oficial CTI como conjunto, não uma busca textual pela frase temática da pergunta. Pedido por "nossas vendas" significa o conjunto autorizado de vendas, salvo filtro específico explicitamente pedido pelo usuário.
- Nunca descreva registros como "relacionados ao termo", "associados ao termo" ou equivalente quando a consulta executada estiver sem filtro textual.
- Nunca declare ausência de clientes, oportunidades, pedidos, propostas ou outros domínios internos que não tenham sido efetivamente consultados na execução.
- Em análise multi-fonte, organize a resposta em três camadas sem misturá-las: fatos externos verificados; dados internos CTI; cruzamento e implicações comerciais. A terceira camada é inferência/recomendação e deve ser apresentada como tal.
- Se as fontes não permitirem um cruzamento pedido, declare a limitação em vez de preencher a lacuna por conhecimento prévio.
- Catálogo CTI representa portfólio atual; ANFIR/território representam registros históricos do recorte; vendas/CRM representam registros operacionais. Não troque o papel dessas fontes.
- Não calcule share, liderança ou participação de mercado sem denominador compatível e explicitamente consultado.
"""

_WEB_ENTIDADES_IGNORADAS = {
    "brasil", "brasileiro", "brasileira", "mercado", "transporte", "refrigerado", "refrigerada",
    "refrigeração", "refrigeracao", "tecnologia", "tecnologias", "fabricante", "fabricantes",
    "série", "serie", "dados", "externos", "verificados", "pedido", "cliente", "carrier", "trailer",
    "equipamento", "equipamentos", "venda", "vendas", "modelo", "linha", "linhas", "monitoramento",
    "digital", "sustentável", "sustentavel", "eficiência", "eficiencia", "fatos", "dados", "internos",
    "cti", "cruzamento", "implicações", "implicacoes", "comerciais", "não", "nao", "uma", "mais",
}


def _eh_multifonte(evidencias: set[str] | frozenset[str]) -> bool:
    return "web" in evidencias and bool(set(evidencias) - {"web"})


def _fontes_requeridas_ia004(mensagem: str) -> set[str]:
    requeridas = set(_ORIGINAL_FONTES_IA003(mensagem))
    _EVIDENCIAS_IA004.set(frozenset(requeridas))
    _PERGUNTA_IA004.set(str(mensagem or ""))
    return requeridas


def _dominios_permitidos(evidencias: set[str]) -> set[str]:
    permitidos = evidencias & _DOMINIOS_CTI
    if "relacionamentos_vendas" in evidencias:
        permitidos.add("vendas")
    return permitidos


def _ferramentas_permitidas_multifonte(evidencias: set[str]) -> tuple[list[dict[str, Any]], set[str]]:
    ferramentas = _ORIGINAL_FERRAMENTAS_CRM()
    if not _eh_multifonte(evidencias):
        return ferramentas, set()

    nomes: set[str] = set()
    if "web" in evidencias:
        nomes.add("web_search")
    if evidencias & {"cti_atual", "resumo_cti"}:
        nomes.add("consultar_resumo_cti")
    if "historico" in evidencias:
        nomes.add("consultar_historico_cti")
    if "territorio" in evidencias:
        nomes.add("consultar_territorio_cti")
    if "anfir" in evidencias:
        nomes.add("consultar_anfir_cti")
    if "produtos" in evidencias:
        nomes.add("consultar_catalogo_produtos_cti")

    dominios = _dominios_permitidos(evidencias)
    if dominios:
        nomes.add("consultar_dominio_cti")

    resultado: list[dict[str, Any]] = []
    for ferramenta in ferramentas:
        tipo = ferramenta.get("type")
        nome = "web_search" if tipo == "web_search" else str(ferramenta.get("name") or "")
        if nome not in nomes:
            continue
        item = deepcopy(ferramenta)
        if nome == "consultar_dominio_cti" and dominios:
            try:
                item["parameters"]["properties"]["dominio"]["enum"] = sorted(dominios)
            except (KeyError, TypeError):
                pass
        resultado.append(item)
    return resultado, nomes


def _ferramentas_base_ia004() -> list[dict[str, Any]]:
    evidencias = set(_EVIDENCIAS_IA004.get())
    ferramentas, _ = _ferramentas_permitidas_multifonte(evidencias)
    return ferramentas


def _normalizar_argumentos_multifonte(
    nome: str,
    argumentos: dict[str, Any],
    evidencias: set[str],
    pergunta: str,
) -> dict[str, Any]:
    resultado = dict(argumentos or {})
    if not _eh_multifonte(evidencias):
        return resultado

    texto = str(pergunta or "").casefold()
    portfolio_amplo = any(t in texto for t in ("nosso portfólio", "nosso portfolio", "catálogo do cti", "catalogo do cti"))
    vendas_amplas = any(t in texto for t in ("nossas vendas", "minhas vendas", "vendas do cti", "vendas no cti"))

    if nome == "consultar_catalogo_produtos_cti" and "produtos" in evidencias and portfolio_amplo:
        resultado["termo"] = None

    if (
        nome == "consultar_dominio_cti"
        and "vendas" in evidencias
        and str(resultado.get("dominio") or "") == "vendas"
        and vendas_amplas
    ):
        resultado["termo"] = None
        resultado["status"] = None
        resultado["offset"] = 0
        resultado["limite"] = max(100, int(resultado.get("limite") or 100))

    return resultado


def _executar_ferramenta_ia004(nome: str, argumentos: dict[str, Any], usuario_id: str, tipo_usuario: str) -> dict[str, Any]:
    evidencias = set(_EVIDENCIAS_IA004.get())
    pergunta = _PERGUNTA_IA004.get()
    normalizados = _normalizar_argumentos_multifonte(nome, argumentos, evidencias, pergunta)
    argumentos.clear()
    argumentos.update(normalizados)
    return _ORIGINAL_EXECUTAR_FERRAMENTA(nome, argumentos, usuario_id, tipo_usuario)


def _instrucao_sintese_ia004(evidencias: set[str]) -> str:
    instrucao = _ORIGINAL_INSTRUCAO_SINTESE_CRM(evidencias)
    if not _eh_multifonte(evidencias):
        return instrucao
    return (
        instrucao
        + " INSTRUÇÃO INTERNA IA-004: produza a resposta final separando claramente: "
        "(1) FATOS EXTERNOS VERIFICADOS, citando apenas fatos sustentados pela web desta execução; "
        "(2) DADOS INTERNOS CTI, limitados aos domínios realmente consultados; "
        "(3) CRUZAMENTO E IMPLICAÇÕES COMERCIAIS, explicitamente tratados como inferências/recomendações. "
        "Quando produtos forem exigidos por pedido de nosso portfólio, trate o catálogo retornado como conjunto do portfólio atual, sem transformar busca textual vazia em ausência geral. "
        "Quando vendas forem consultadas sem termo, descreva-as como vendas retornadas no universo autorizado; nunca invente um termo de busca para qualificá-las. "
        "Não declare ausência de clientes, oportunidades, pedidos, propostas ou outros domínios que não estejam entre as evidências desta execução. "
        "Não use uma origem para provar fato pertencente à outra e qualifique qualquer ausência pelo recorte consultado."
    )


def _auditar_ferramentas_multifonte(metadados: dict[str, Any], evidencias: set[str]) -> None:
    if not _eh_multifonte(evidencias):
        return

    _, nomes_permitidos = _ferramentas_permitidas_multifonte(evidencias)
    dominios_permitidos = _dominios_permitidos(evidencias)
    indevidas: list[str] = []

    for item in metadados.get("ferramentas") or []:
        if not isinstance(item, dict) or item.get("tipo") != "CTI":
            continue
        nome = str(item.get("ferramenta") or "")
        if nome not in nomes_permitidos:
            indevidas.append(nome or "ferramenta_cti_desconhecida")
            continue
        if nome == "consultar_dominio_cti":
            dominio = str((item.get("argumentos") or {}).get("dominio") or "")
            if dominio not in dominios_permitidos:
                indevidas.append(f"consultar_dominio_cti:{dominio}")

    if indevidas:
        raise base.IAComercialOpenAIError(
            "A execução multi-fonte tentou consultar uma fonte interna fora do escopo solicitado.",
            codigo="AGENT_MULTISOURCE_SCOPE_VIOLATION",
        )


def _sanitizar_ausencias_nao_consultadas(texto: str, evidencias: set[str]) -> tuple[str, int]:
    linhas = str(texto or "").splitlines()
    removidas = 0
    dom = {
        "clientes": ("cliente", "clientes", "carteira"),
        "oportunidades": ("oportunidade", "oportunidades", "pipeline"),
        "pedidos": ("pedido", "pedidos"),
        "propostas": ("proposta", "propostas"),
        "atividades": ("atividade", "atividades", "visita", "visitas"),
    }
    marcadores_ausencia = (
        "não há", "nao ha", "não foram encontr", "nao foram encontr", "nenhum", "nenhuma",
        "não existem", "nao existem", "ausência", "ausencia", "sem registros",
    )

    resultado: list[str] = []
    for linha in linhas:
        norm = linha.casefold()
        nao_sustentada = False
        if any(m in norm for m in marcadores_ausencia):
            for evidencia, termos in dom.items():
                if evidencia not in evidencias and any(t in norm for t in termos):
                    nao_sustentada = True
                    break
        if nao_sustentada:
            removidas += 1
            continue
        resultado.append(linha)

    if removidas:
        resultado.append("")
        resultado.append(
            "Limitação de evidência: clientes, oportunidades e demais domínios não consultados nesta execução não podem ser classificados como ausentes."
        )
    return "\n".join(resultado).strip(), removidas


def _vendas_foram_consultadas_sem_termo(metadados: dict[str, Any]) -> bool:
    consultas = []
    for item in metadados.get("ferramentas") or []:
        if not isinstance(item, dict) or item.get("tipo") != "CTI":
            continue
        if item.get("ferramenta") != "consultar_dominio_cti":
            continue
        argumentos = item.get("argumentos") or {}
        if str(argumentos.get("dominio") or "") == "vendas":
            consultas.append(argumentos)
    return bool(consultas) and all(not str(item.get("termo") or "").strip() for item in consultas)


def _sanitizar_filtros_inexistentes(texto: str, metadados: dict[str, Any]) -> tuple[str, int]:
    if not _vendas_foram_consultadas_sem_termo(metadados):
        return str(texto or ""), 0

    padrao = re.compile(
        r"\s+(?:relacionad[ao]s?|associad[ao]s?|vinculad[ao]s?)\s+ao\s+termo\s+[\"“'][^\"”']+[\"”']",
        flags=re.IGNORECASE,
    )
    ajustado, quantidade = padrao.subn("", str(texto or ""))
    return ajustado, quantidade


def _entidades_web_linha(linha: str) -> list[str]:
    entidades: list[str] = []
    for token in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ0-9_-]{3,}\b", str(linha or "")):
        normalizado = token.casefold()
        if normalizado in _WEB_ENTIDADES_IGNORADAS:
            continue
        entidades.append(normalizado)
    return list(dict.fromkeys(entidades))


def _fonte_web_compativel(linha: str, fontes_web: list[dict[str, Any]]) -> bool:
    entidades = _entidades_web_linha(linha)
    if not entidades:
        return True
    corpus = " ".join(
        f"{str(fonte.get('descricao') or '')} {str(fonte.get('url') or '')}".casefold()
        for fonte in fontes_web
        if isinstance(fonte, dict)
    )
    return any(entidade in corpus for entidade in entidades)


def _sanitizar_fatos_web_sem_proveniencia(texto: str, fontes_web: list[dict[str, Any]]) -> tuple[str, int]:
    linhas = str(texto or "").splitlines()
    resultado: list[str] = []
    secao_web = False
    removidas = 0

    for linha in linhas:
        normalizada = linha.strip().casefold()
        if "fatos externos verificados" in normalizada:
            secao_web = True
            resultado.append(linha)
            continue
        if "dados internos cti" in normalizada or "cruzamento e implica" in normalizada:
            secao_web = False
            resultado.append(linha)
            continue
        if secao_web and linha.strip().startswith(("-", "•", "*")) and not _fonte_web_compativel(linha, fontes_web):
            removidas += 1
            continue
        resultado.append(linha)

    return "\n".join(resultado).strip(), removidas


def _historico_para_execucao_web(historico: list[dict[str, str]], evidencias_previstas: set[str]) -> list[dict[str, str]]:
    if "web" not in evidencias_previstas:
        return historico
    somente_usuario = [
        item for item in historico
        if str(item.get("role") or "").casefold() == "user" and str(item.get("content") or "").strip()
    ]
    return somente_usuario[-12:]


def _gerar_base_ia004(
    mensagem: str,
    historico: list[dict[str, str]],
    usuario_id: str,
    tipo_usuario: str,
):
    pergunta_original = base._mensagem_original_para_evidencias(mensagem)
    evidencias_previstas = set(_fontes_requeridas_ia004(pergunta_original))
    historico_execucao = _historico_para_execucao_web(historico, evidencias_previstas)
    texto, metadados = _ORIGINAL_GERAR_BASE(mensagem, historico_execucao, usuario_id, tipo_usuario)
    evidencias = set(str(x) for x in (metadados.get("evidencias_requeridas") or _EVIDENCIAS_IA004.get()))
    if "web" in evidencias_previstas:
        metadados["controle_historico_web"] = "somente_turnos_usuario_sem_respostas_web_anteriores"
        metadados["historico_web_mensagens_utilizadas"] = len(historico_execucao)
    if not _eh_multifonte(evidencias):
        return texto, metadados

    _auditar_ferramentas_multifonte(metadados, evidencias)
    texto, ajustes_ausencia = _sanitizar_ausencias_nao_consultadas(texto, evidencias)
    texto, ajustes_filtro = _sanitizar_filtros_inexistentes(texto, metadados)
    fontes_web = [
        fonte for fonte in (metadados.get("fontes") or [])
        if isinstance(fonte, dict) and fonte.get("url")
    ]
    texto, ajustes_web = _sanitizar_fatos_web_sem_proveniencia(texto, fontes_web)
    internas = sorted(evidencias - {"web"})
    metadados.update(
        {
            "controle_multifonte": "ia004_fontes_restritas_e_proveniencia",
            "multifonte_evidencias_requeridas": sorted(evidencias),
            "multifonte_fontes_internas": internas,
            "multifonte_fontes_web": len(fontes_web),
            "controle_multifonte_proveniencia": "externo_interno_inferencia_segregados",
            "controle_inferencia_multifonte": "inferencia_nao_e_evidencia",
            "controle_ausencia_multifonte": "ausencia_limitada_a_fonte_e_recorte_consultados",
            "controle_consulta_portfolio": "catalogo_completo_quando_portfolio_amplo",
            "controle_consulta_vendas": "universo_autorizado_quando_vendas_amplas",
            "controle_filtros_multifonte": "qualificacao_textual_somente_se_filtro_executado",
            "controle_web_por_afirmacao": "entidade_compativel_com_titulo_ou_url_da_execucao",
            "multifonte_ajustes_ausencia_nao_consultada": ajustes_ausencia,
            "multifonte_ajustes_filtro_inexistente": ajustes_filtro,
            "multifonte_ajustes_web_sem_proveniencia": ajustes_web,
        }
    )
    return texto, metadados


crm._fontes_requeridas_ia003 = _fontes_requeridas_ia004
crm._ORIGINAL_FERRAMENTAS_AGENTE = _ferramentas_base_ia004
crm._ORIGINAL_INSTRUCOES_AGENTE = _ORIGINAL_INSTRUCOES_CRM + _INSTRUCOES_IA004
crm._ORIGINAL_INSTRUCAO_SINTESE = _instrucao_sintese_ia004
base._executar_ferramenta_cti = _executar_ferramenta_ia004
base.gerar_resposta_agente = _gerar_base_ia004


def sintetizar_fatos_execucao(
    pergunta_atual: str,
    metadados: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
):
    evidencias = {str(x) for x in (metadados.get("evidencias_atendidas") or [])}
    requeridas = {str(x) for x in (metadados.get("evidencias_requeridas") or [])}
    fontes_web = [
        fonte for fonte in (metadados.get("fontes") or [])
        if isinstance(fonte, dict) and fonte.get("url")
    ]

    if _eh_multifonte(requeridas):
        return None, {
            "controle_sintese_factual": "ia004_multifonte_preservada_com_proveniencia",
            "controle_multifonte": "ia004_fontes_restritas_e_proveniencia",
            "controle_multifonte_proveniencia": "externo_interno_inferencia_segregados",
            "multifonte_fontes_internas_sintese": sorted(requeridas - {"web"}),
            "web_fontes_sintese": len(fontes_web),
            "web_urls_sintese": [str(fonte.get("url")) for fonte in fontes_web],
            "crm_evidencias": sorted(evidencias & EVIDENCIAS_CRM),
        }

    if "web" in evidencias:
        return None, {
            "controle_sintese_factual": "ia003_web_preservada_agente_com_fontes",
            "controle_web_proveniencia": "fontes_url_execucao_atual",
            "web_fontes_sintese": len(fontes_web),
            "web_urls_sintese": [str(fonte.get("url")) for fonte in fontes_web],
            "crm_evidencias": sorted(evidencias & EVIDENCIAS_CRM),
        }

    if evidencias & EVIDENCIAS_CRM:
        return None, {
            "controle_sintese_factual": "crm_operacional_semantico_preservado",
            "controle_crm_operacional": "semantica_backend_e_vinculos_resolvidos",
            "crm_evidencias": sorted(evidencias & EVIDENCIAS_CRM),
        }
    return sintetizar_fatos_base(pergunta_atual, metadados, usuario_id, tipo_usuario)