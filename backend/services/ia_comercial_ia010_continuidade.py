from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from . import ia_comercial_agente_crm as _crm
from . import ia_comercial_agente as _base
from .ia_comercial_conhecimento_semantico import buscar_conhecimento_relevante


_ORIGINAL_GERAR = _crm.gerar_resposta_agente
_ORIGINAL_FERRAMENTAS = _crm._ferramentas_universais
_USAR_CTI: ContextVar[bool] = ContextVar("ia010_usar_cti", default=True)


_INSTRUCOES_IA010 = """

IA-010 — ROTEAMENTO POR RELEVÂNCIA E MEMÓRIA SEMÂNTICA:
- O CTI é uma fonte disponível, não uma fonte obrigatória em toda resposta.
- Não consulte catálogo, CRM, histórico, ANFIR ou outras fontes internas apenas para tentar encontrar relação com um documento recebido.
- Consulte o CTI somente quando a pergunta pedir explicitamente dados internos, quando houver entidade interna concreta a verificar, ou quando uma conclusão realmente dependa de informação operacional existente no sistema.
- A ausência de um assunto, solução, produto, empresa ou termo nas fontes internas não deve ser mencionada se essa ausência não responder materialmente à pergunta do usuário.
- Em pedidos de análise documental e comparação de mercado, priorize: conteúdo do documento -> fontes externas atuais necessárias -> comparação -> conclusões úteis. Use CTI apenas se houver necessidade factual interna real.
- Conhecimento documental acumulado pela IA é diferente de verdade operacional. Ele pode sustentar análise futura com sua proveniência e SHA-256, mas nunca cria cliente, oportunidade, proposta, pedido, venda ou outro registro operacional.
- Quando houver memória semântica relevante, use-a como conhecimento documental já adquirido. Não peça reenvio do documento apenas porque ele não existe em uma entidade operacional.
- Se a memória acumulada e uma fonte mais atual divergirem, preserve as duas proveniências, informe a divergência e dê precedência temporal adequada ao fato que estiver sendo tratado.
"""


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _precisa_cti_explicito(mensagem: str) -> bool:
    texto = _normalizar(mensagem)
    marcadores_internos = (
        "cti", "crm", "pipeline", "carteira", "meus clientes", "nossos clientes", "cliente no sistema",
        "clientes no sistema", "dados internos", "base interna", "cadastro interno", "histórico comercial",
        "historico comercial", "vendas registradas", "pedidos registrados", "propostas registradas",
        "oportunidades registradas", "responsabilidade comercial", "responsável comercial", "responsavel comercial",
        "anfir", "ddd", "território", "territorio", "região comercial", "regiao comercial",
    )
    return any(marcador in texto for marcador in marcadores_internos)


def _eh_analise_documental_ou_mercado(mensagem: str) -> bool:
    texto = _normalizar(mensagem)
    return any(
        marcador in texto
        for marcador in (
            "arquivo", "anexo", "pdf", "planilha", "apresentação", "apresentacao", "documento",
            "concorrente", "concorrentes", "concorrência", "concorrencia", "benchmark",
            "comparar com a oferta", "compare com a oferta", "o que estão ofertando", "o que estao ofertando",
        )
    )


def _precisa_web(mensagem: str) -> bool:
    texto = _normalizar(mensagem)
    if _crm._necessita_web(mensagem):
        return True
    return any(
        marcador in texto
        for marcador in (
            "concorrente", "concorrentes", "concorrência", "concorrencia", "comparar com a oferta",
            "compare com a oferta", "o que estão ofertando", "o que estao ofertando", "benchmark",
        )
    )


def _fontes_requeridas_ia010(mensagem: str) -> set[str]:
    if _crm._somente_web_explicito(mensagem):
        return {"web"}

    requeridas: set[str] = set()
    cti_explicito = _precisa_cti_explicito(mensagem)
    analise_externa = _eh_analise_documental_ou_mercado(mensagem)

    # Preserva o comportamento universal para perguntas operacionais livres do CTI,
    # mas não transforma todo documento/benchmark em busca interna obrigatória.
    if cti_explicito or not analise_externa:
        requeridas.update({"catalogo_cti", "universo_cti"})
    if _precisa_web(mensagem):
        requeridas.add("web")
    return requeridas


def _ferramentas_ia010() -> list[dict[str, Any]]:
    ferramentas = _ORIGINAL_FERRAMENTAS()
    if _USAR_CTI.get():
        return ferramentas
    return [
        item
        for item in ferramentas
        if not (
            item.get("type") == "function"
            and item.get("name") in {"catalogar_universo_cti", "consultar_universo_cti"}
        )
    ]


def _anexar_memoria(mensagem: str, usuario_id: str, tipo_usuario: str) -> tuple[str, list[dict[str, Any]]]:
    pergunta_original = _base._mensagem_original_para_evidencias(mensagem)
    contexto, fontes = buscar_conhecimento_relevante(
        pergunta_original,
        usuario_id=usuario_id,
        tipo_usuario=tipo_usuario,
    )
    if not contexto:
        return mensagem, []
    return f"{mensagem}\n\n{contexto}", fontes


def gerar_resposta_agente(mensagem: str, historico: list[dict[str, str]], usuario_id: str, tipo_usuario: str):
    pergunta_original = _base._mensagem_original_para_evidencias(mensagem)
    requeridas = _fontes_requeridas_ia010(pergunta_original)
    token = _USAR_CTI.set("universo_cti" in requeridas)
    try:
        mensagem_com_memoria, fontes_memoria = _anexar_memoria(mensagem, usuario_id, tipo_usuario)
        texto, metadados = _ORIGINAL_GERAR(mensagem_com_memoria, historico, usuario_id, tipo_usuario)
    finally:
        _USAR_CTI.reset(token)

    if fontes_memoria:
        fontes = [item for item in (metadados.get("fontes") or []) if isinstance(item, dict)]
        existentes = {
            (str(item.get("tipo") or ""), str(item.get("sha256") or ""), str(item.get("url") or ""))
            for item in fontes
        }
        for fonte in fontes_memoria:
            chave = ("CONHECIMENTO_IA", str(fonte.get("sha256") or ""), "")
            if chave not in existentes:
                fontes.append({
                    "tipo": "CONHECIMENTO_IA",
                    "descricao": f"Memória semântica: {fonte.get('nome')} · SHA-256 {str(fonte.get('sha256') or '')[:12]}…",
                    "sha256": fonte.get("sha256"),
                    "documento_id": fonte.get("documento_id"),
                    "escopo": fonte.get("escopo"),
                })
        metadados["fontes"] = fontes
        metadados["conhecimento_semantico_usado"] = fontes_memoria
    else:
        metadados["conhecimento_semantico_usado"] = []

    metadados["controle_roteamento_ia010"] = "cti_condicional_por_relevancia"
    metadados["cti_requerido_ia010"] = "universo_cti" in requeridas
    metadados["controle_memoria_semantica"] = "documental_persistente_nao_operacional"
    return texto, metadados


_crm._fontes_requeridas_universais = _fontes_requeridas_ia010
_crm._ferramentas_universais = _ferramentas_ia010
_crm._pede_cruzamento_cti_explicito = _precisa_cti_explicito
_crm.gerar_resposta_agente = gerar_resposta_agente
if _INSTRUCOES_IA010 not in _crm._INSTRUCOES_UNIVERSAIS:
    _crm._INSTRUCOES_UNIVERSAIS += _INSTRUCOES_IA010
