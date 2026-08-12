from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.ia_comercial_acoes_router import (
    ConfirmarAcaoRequest,
    ProporAcaoRequest,
    cancelar_acao,
    confirmar_acao,
    propor_acao,
)
from services.ia_comercial_agente_crm import gerar_resposta_agente
from services.ia_comercial_auditoria_evidencial import construir_auditoria_evidencial
from services.ia_comercial_cti import IAComercialOpenAIError
from services.ia_comercial_sintese_crm import sintetizar_fatos_execucao

router = APIRouter(prefix="/ia-comercial-cti", tags=["IA Comercial CTI"])

_HISTORICO_MAX_MENSAGENS = 24
_HISTORICO_MAX_CARACTERES_POR_MENSAGEM = 8000
_RE_CONFIRMACAO_ACAO = re.compile(r"^\s*confirmar\s+a[cç][aã]o\s+([0-9a-f-]{36})\s*[.!]?\s*$", re.I)
_RE_CANCELAMENTO_ACAO = re.compile(r"^\s*cancelar\s+a[cç][aã]o\s+([0-9a-f-]{36})\s*[.!]?\s*$", re.I)
_RE_NUMERO_PEDIDO = re.compile(r"\bPED-\d{8}-[A-Z0-9]+\b", re.I)


class NovaConversa(BaseModel):
    titulo: str = Field(default="Nova conversa", max_length=120)


class NovaMensagem(BaseModel):
    mensagem: str = Field(min_length=1, max_length=12000)


def _dados(resposta):
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _periodo_temporal_explicito(mensagem: str) -> bool:
    texto = mensagem.strip().casefold()
    if not texto:
        return False

    expressoes = (
        r"\bhoje\b",
        r"\b(?:últim|ultim)[oa]s?\s+\d+\s+(?:dias?|semanas?|meses?|anos?)\b",
        r"\b(?:este|neste|no)\s+m[eê]s\b",
        r"\bm[eê]s\s+atual\b",
        r"\b(?:este|neste|no)\s+trimestre\b",
        r"\btrimestre\s+atual\b",
        r"\b(?:este|neste|no)\s+ano\b",
        r"\bano\s+atual\b",
        r"\btodo\s+(?:o\s+)?hist[oó]rico\b",
        r"\bhist[oó]rico\s+completo\b",
        r"\b20\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b20\d{2}-\d{2}-\d{2}\b",
    )
    return any(re.search(expressao, texto) for expressao in expressoes)


def _mensagem_com_contexto_temporal(mensagem: str) -> tuple[str, str]:
    if _periodo_temporal_explicito(mensagem):
        controle = "periodo_explicito_usuario"
        instrucao_temporal = (
            "CONTEXTO INTERNO DA IA CTI: a pergunta contém um horizonte temporal "
            "explicitamente definido pelo usuário. Preserve esse horizonte nas consultas; "
            "não o substitua silenciosamente por outro período."
        )
    else:
        controle = "sem_periodo_explicito_todo_historico"
        instrucao_temporal = (
            "CONTEXTO INTERNO DA IA CTI: a pergunta não definiu um horizonte temporal concreto. "
            "Para consultas territoriais/ANFIR, use TODO_HISTORICO como universo-base dos dados "
            "disponíveis. Janelas recentes podem ser analisadas complementarmente quando forem úteis, "
            "mas não podem substituir silenciosamente o universo histórico disponível. "
            "Este contexto pertence exclusivamente ao módulo IA Comercial e não deriva de filtros, "
            "estado ou ações de outros módulos do CTI."
        )

    instrucao_recorte = (
        " REGRA DE RECORTE-BASE E PROVENIÊNCIA: ao construir o universo-base de consultas territoriais "
        "ou ANFIR, aplique como filtros restritivos somente dimensões explicitamente informadas na pergunta "
        "atual. Não acrescente fabricante, cliente, implementadora, modelo, cidade, UF, origem ou outra "
        "restrição por inferência para definir ou substituir o universo-base. Recortes exploratórios adicionais "
        "são permitidos somente depois de coletar o universo-base e devem ser tratados como análises "
        "complementares, sem apagar ou substituir os totais do recorte-base. Preserve a proveniência entre "
        "fontes: catálogo oficial informa portfólio/modelos disponíveis, mas não prova que um modelo aparece "
        "no histórico ANFIR; só atribua modelo ao histórico quando o próprio registro histórico sustentar isso. "
        "Da mesma forma, clientes do CRM podem servir como contexto ou candidatos comerciais, mas não devem "
        "ser apresentados como pertencentes ao recorte territorial pesquisado sem vínculo territorial explícito "
        "nos dados retornados."
        " REGRA DE PRECISÃO FACTUAL: não transforme ausência de dado em confirmação. Se um campo estiver vazio, "
        "nulo ou ausente, declare a ausência quando ela for relevante e não atribua categoria, status ou fato não "
        "registrado. Use 'maioria', 'predominante', 'líder', 'principal' ou equivalentes somente quando uma categoria "
        "representar estritamente mais de 50% do universo considerado. Quando a cobertura do campo for parcial, "
        "informe a contagem exata sobre o universo total ou qualifique explicitamente como 'entre os registros "
        "preenchidos'; não transforme a categoria mais frequente entre preenchidos em predominância do universo. "
        "Em empate ou pluralidade sem maioria absoluta, informe as contagens/percentuais sem chamar nenhuma categoria "
        "de majoritária ou predominante. Não converta status operacional, administrativo ou documental em venda, "
        "negócio realizado, aceite, entrega ou outro evento comercial sem semântica explícita da fonte que sustente "
        "essa equivalência. Só qualifique cliente como ativo/inativo quando o status correspondente estiver "
        "explicitamente preenchido na fonte consultada. Ao descrever cobertura de campos, use contagens exatas "
        "quando disponíveis: por exemplo, se todos os registros do recorte estão sem modelo, diga que todos estão "
        "sem modelo ou informe X de X, e não 'na maioria dos casos'."
        " REGRA DE EVIDÊNCIA DA EXECUÇÃO ATUAL: o histórico da conversa pode ser usado para compreender continuidade, "
        "resolver referências como 'esse cliente', 'esse pedido', 'o anterior' e preservar a intenção já estabelecida, "
        "mas nunca conta como evidência factual da execução atual. Toda afirmação factual sobre estado operacional, "
        "dados CTI ou fatos externos que exija validação deve ser sustentada por fonte efetivamente consultada nesta "
        "execução. Ao receber uma pergunta factual de continuidade, use o histórico apenas para identificar o referente "
        "e reconsulte a ferramenta adequada antes de responder. Não reutilize silenciosamente números, status, vendas, "
        "pipeline, catálogo, ANFIR, território ou fatos web de respostas anteriores como se fossem evidência atual."
    )
    return f"{mensagem}\n\n{instrucao_temporal}{instrucao_recorte}", controle


def _conversa_do_usuario(conversa_id: str, usuario: UsuarioAutenticado) -> dict:
    resposta = (
        supabase.table("cti_ia_conversas")
        .select("*")
        .eq("id", conversa_id)
        .eq("usuario_id", usuario.id)
        .limit(1)
        .execute()
    )
    linhas = _dados(resposta)
    if not linhas:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    return linhas[0]


def _historico_conversacional(conversa_id: str, usuario: UsuarioAutenticado) -> list[dict[str, str]]:
    linhas = _dados(
        supabase.table("cti_ia_mensagens")
        .select("papel,conteudo,created_at")
        .eq("conversa_id", conversa_id)
        .eq("usuario_id", usuario.id)
        .order("created_at", desc=True)
        .limit(_HISTORICO_MAX_MENSAGENS)
        .execute()
    )
    historico: list[dict[str, str]] = []
    for item in reversed(linhas):
        papel = str(item.get("papel") or "").strip().casefold()
        conteudo = str(item.get("conteudo") or "").strip()
        if papel not in {"user", "assistant"} or not conteudo:
            continue
        historico.append(
            {
                "role": papel,
                "content": conteudo[:_HISTORICO_MAX_CARACTERES_POR_MENSAGEM],
            }
        )
    return historico


def _renderizar_plano_validado(metadados: dict) -> str | None:
    if not metadados.get("planejamento_comercial_ativo"):
        return None
    plano = metadados.get("plano_comercial") or {}
    acoes = plano.get("acoes") or []
    if not isinstance(acoes, list) or not acoes:
        return None

    linhas = ["PLANO COMERCIAL ESTRUTURADO"]
    objetivo = str(plano.get("objetivo") or "").strip()
    if objetivo:
        linhas.append(objetivo)

    for item in acoes:
        if not isinstance(item, dict):
            continue
        ordem = item.get("ordem")
        prioridade = str(item.get("prioridade") or "MEDIA")
        horizonte = str(item.get("horizonte") or "CURTO_PRAZO")
        acao = str(item.get("acao") or "").strip()
        if not acao:
            continue
        fundamentos = [str(x) for x in (item.get("fundamentos") or []) if str(x)]
        qualificacao = str(item.get("qualificacao_evidencial") or "EVIDENCIA_COMPLETA")
        base = f"base: {', '.join(fundamentos)}; evidência: {qualificacao}" if fundamentos else f"evidência: {qualificacao}"
        linhas.append(f"{ordem}. [{prioridade} | {horizonte}] {acao} ({base})")
        dependencias = [str(x) for x in (item.get("dependencias") or []) if str(x).strip()]
        riscos = [str(x) for x in (item.get("riscos") or []) if str(x).strip()]
        resultado = str(item.get("resultado_esperado") or "").strip()
        lacunas = [str(x) for x in (item.get("lacunas_evidenciais") or []) if str(x).strip()]
        if dependencias:
            linhas.append("   Dependências: " + "; ".join(dependencias))
        if riscos:
            linhas.append("   Riscos: " + "; ".join(riscos))
        if resultado:
            linhas.append("   Resultado esperado: " + resultado)
        if lacunas:
            linhas.append("   Lacunas evidenciais: " + ", ".join(lacunas))

    return "\n".join(linhas).strip()


def _registrar_mensagem_usuario(conversa_id: str, usuario: UsuarioAutenticado, mensagem: str) -> None:
    supabase.table("cti_ia_mensagens").insert(
        {
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "papel": "user",
            "conteudo": mensagem,
            "fontes": [],
            "metadados": {},
        }
    ).execute()


def _resposta_direta(
    conversa_id: str,
    usuario: UsuarioAutenticado,
    conteudo: str,
    metadados: dict,
) -> dict:
    criado = _dados(
        supabase.table("cti_ia_mensagens")
        .insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "papel": "assistant",
                "conteudo": conteudo,
                "fontes": [],
                "metadados": metadados,
            }
        )
        .execute()
    )
    supabase.table("cti_ia_conversas").update(
        {"updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", conversa_id).execute()
    supabase.table("cti_ia_auditoria").insert(
        {
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "acao": "IA008_INTERACAO_CONTROLADA",
            "detalhes": metadados,
        }
    ).execute()
    return criado[0] if criado else {
        "conversa_id": conversa_id,
        "papel": "assistant",
        "conteudo": conteudo,
        "fontes": [],
        "metadados": metadados,
    }


def _proposta_atividade_conversacional(
    conversa_id: str,
    mensagem: str,
    usuario: UsuarioAutenticado,
) -> dict | None:
    texto = mensagem.casefold()
    pede_registro = any(t in texto for t in ("registre", "registrar", "crie", "criar"))
    pede_atividade = any(t in texto for t in ("atividade", "acompanhamento", "visita"))
    if not (pede_registro and pede_atividade):
        return None

    numero_match = _RE_NUMERO_PEDIDO.search(mensagem)
    if not numero_match:
        return None
    numero = numero_match.group(0).upper()
    pedidos = _dados(
        supabase.table("cti_pedidos")
        .select("id,numero,cliente_id")
        .eq("numero", numero)
        .limit(1)
        .execute()
    )
    if not pedidos:
        return None
    pedido = pedidos[0]
    tipo = "VISITA" if "visita" in texto else "ACOMPANHAMENTO"
    titulo = f"{tipo.title()} do pedido {numero}"
    return propor_acao(
        ProporAcaoRequest(
            conversa_id=conversa_id,
            tipo_acao="CRIAR_ATIVIDADE_CRM",
            payload={
                "cliente_id": pedido.get("cliente_id"),
                "pedido_id": pedido.get("id"),
                "tipo": tipo,
                "titulo": titulo,
                "descricao": mensagem,
            },
        ),
        usuario,
    )


def _tratar_acao_controlada(
    conversa_id: str,
    mensagem: str,
    usuario: UsuarioAutenticado,
) -> dict | None:
    confirmar_match = _RE_CONFIRMACAO_ACAO.match(mensagem)
    if confirmar_match:
        resultado = confirmar_acao(
            confirmar_match.group(1),
            ConfirmarAcaoRequest(confirmar=True),
            usuario,
        )
        registro = (resultado.get("resultado") or {}).get("registro") or {}
        registro_id = registro.get("id")
        conteudo = "AÇÃO CONTROLADA EXECUTADA\nA confirmação foi validada e a ação foi executada uma única vez."
        if registro_id:
            conteudo += f"\nRegistro criado/atualizado: {registro_id}."
        return _resposta_direta(
            conversa_id,
            usuario,
            conteudo,
            {
                "controle_acao_controlada": "ia008_confirmacao_explicita_executada",
                "acao_id": confirmar_match.group(1),
                "status": "EXECUTADA",
                "idempotencia": resultado.get("idempotencia") or "EXECUCAO_UNICA",
                "resultado": resultado.get("resultado"),
            },
        )

    cancelar_match = _RE_CANCELAMENTO_ACAO.match(mensagem)
    if cancelar_match:
        resultado = cancelar_acao(cancelar_match.group(1), usuario)
        return _resposta_direta(
            conversa_id,
            usuario,
            "AÇÃO CONTROLADA CANCELADA\nNenhuma alteração operacional foi executada.",
            {
                "controle_acao_controlada": "ia008_cancelamento_explicito",
                "acao_id": cancelar_match.group(1),
                "status": resultado.get("status"),
            },
        )

    proposta = _proposta_atividade_conversacional(conversa_id, mensagem, usuario)
    if proposta:
        acao_id = str(proposta.get("acao_id") or "")
        conteudo = (
            "AÇÃO CONTROLADA PENDENTE DE CONFIRMAÇÃO\n"
            f"{proposta.get('resumo')}\n"
            "Nenhuma alteração foi executada ainda.\n"
            f"Para executar, responda exatamente: CONFIRMAR AÇÃO {acao_id}\n"
            f"Para desistir, responda: CANCELAR AÇÃO {acao_id}"
        )
        return _resposta_direta(
            conversa_id,
            usuario,
            conteudo,
            {
                "controle_acao_controlada": "ia008_proposta_pendente_confirmacao",
                "acao_id": acao_id,
                "status": "PENDENTE_CONFIRMACAO",
                "tipo_acao": proposta.get("tipo_acao"),
                "confirmacao_necessaria": True,
            },
        )

    return None


@router.get("/status")
def status_ia(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return {
        "status": "ready",
        "nome": "IA Comercial CTI",
        "modo": "agente_orquestrador_cti_web_acoes_controladas",
        "capacidades": [
            "conversa contextual",
            "escolha autônoma de ferramentas CTI",
            "pesquisa web",
            "cruzamento multi-fonte",
            "continuidade conversacional controlada",
            "cadeia estruturada de evidências",
            "rastreio auditável",
            "planejamento comercial estruturado",
            "ações comerciais controladas com confirmação explícita",
        ],
        "somente_leitura": False,
        "escrita_controlada": True,
        "confirmacao_explicita_para_escrita": True,
        "usuario": {"id": usuario.id, "nome": usuario.nome, "perfil": usuario.tipo_usuario},
    }


@router.get("/conversas")
def listar_conversas(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return _dados(
        supabase.table("cti_ia_conversas")
        .select("*")
        .eq("usuario_id", usuario.id)
        .order("updated_at", desc=True)
        .execute()
    )


@router.post("/conversas")
def criar_conversa(payload: NovaConversa, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    titulo = payload.titulo.strip() or "Nova conversa"
    criado = _dados(
        supabase.table("cti_ia_conversas")
        .insert({"usuario_id": usuario.id, "titulo": titulo, "status": "ATIVA"})
        .execute()
    )
    if not criado:
        raise HTTPException(status_code=500, detail="Não foi possível criar a conversa.")
    return criado[0]


@router.get("/conversas/{conversa_id}/mensagens")
def listar_mensagens(conversa_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _conversa_do_usuario(conversa_id, usuario)
    return _dados(
        supabase.table("cti_ia_mensagens")
        .select("*")
        .eq("conversa_id", conversa_id)
        .order("created_at")
        .execute()
    )


@router.post("/conversas/{conversa_id}/mensagens")
def enviar_mensagem(
    conversa_id: str,
    payload: NovaMensagem,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    conversa = _conversa_do_usuario(conversa_id, usuario)
    mensagem = payload.mensagem.strip()
    historico = _historico_conversacional(conversa_id, usuario)
    _registrar_mensagem_usuario(conversa_id, usuario, mensagem)

    resposta_acao = _tratar_acao_controlada(conversa_id, mensagem, usuario)
    if resposta_acao:
        return resposta_acao

    mensagem_agente, controle_temporal = _mensagem_com_contexto_temporal(mensagem)

    try:
        resposta_texto, metadados = gerar_resposta_agente(
            mensagem=mensagem_agente,
            historico=historico,
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario,
        )
        resposta_factual, metadados_sintese = sintetizar_fatos_execucao(
            pergunta_atual=mensagem,
            metadados=metadados,
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario,
        )
        if resposta_factual:
            resposta_texto = resposta_factual
        metadados.update(metadados_sintese)
        metadados["controle_temporal_pergunta"] = controle_temporal
        metadados["controle_temporal_origem"] = "modulo_ia_comercial"
        metadados["controle_recorte_base"] = "restricoes_explicitas_pergunta"
        metadados["controle_proveniencia_evidencia"] = "fonte_explicita"
        metadados["controle_precisao_factual"] = "qualificacoes_exigem_evidencia_explicita"
        metadados["controle_evidencia_execucao"] = "fatos_somente_fontes_consultadas_na_execucao_atual"
        metadados["controle_historico_agente"] = "ia005_contexto_referencial_nao_evidencial"
        metadados["historico_mensagens_utilizadas"] = len(historico)
        metadados["historico_limite_mensagens"] = _HISTORICO_MAX_MENSAGENS
        metadados.update(construir_auditoria_evidencial(resposta_texto, metadados, mensagem))
        resposta_planejada = _renderizar_plano_validado(metadados)
        if resposta_planejada:
            resposta_texto = resposta_planejada
            metadados["planejamento_texto_renderizado"] = resposta_planejada
            metadados["controle_resposta_planejamento"] = "somente_plano_validado_sem_texto_livre_previo"
    except IAComercialOpenAIError as exc:
        supabase.table("cti_ia_auditoria").insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "acao": "ERRO_OPENAI",
                "detalhes": {"codigo": exc.codigo, "erro": exc.detalhe_tecnico},
            }
        ).execute()
        raise HTTPException(status_code=502, detail=exc.mensagem_publica) from exc
    except Exception as exc:
        supabase.table("cti_ia_auditoria").insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "acao": "ERRO_GERACAO_RESPOSTA",
                "detalhes": {"tipo": type(exc).__name__, "erro": str(exc)[:500]},
            }
        ).execute()
        raise HTTPException(
            status_code=502,
            detail="O núcleo da IA encontrou uma falha interna registrada na auditoria.",
        ) from exc

    fontes = metadados.get("fontes") or []
    assistente = _dados(
        supabase.table("cti_ia_mensagens")
        .insert(
            {
                "conversa_id": conversa_id,
                "usuario_id": usuario.id,
                "papel": "assistant",
                "conteudo": resposta_texto,
                "fontes": fontes,
                "metadados": metadados,
            }
        )
        .execute()
    )
    agora = datetime.now(timezone.utc).isoformat()
    atualizacao = {"updated_at": agora}
    if str(conversa.get("titulo") or "") == "Nova conversa":
        atualizacao["titulo"] = mensagem[:80]
    supabase.table("cti_ia_conversas").update(atualizacao).eq("id", conversa_id).execute()
    supabase.table("cti_ia_auditoria").insert(
        {
            "conversa_id": conversa_id,
            "usuario_id": usuario.id,
            "acao": "RESPOSTA_GERADA_AGENTE",
            "detalhes": metadados,
        }
    ).execute()
    return assistente[0] if assistente else {
        "conversa_id": conversa_id,
        "papel": "assistant",
        "conteudo": resposta_texto,
        "fontes": fontes,
        "metadados": metadados,
    }