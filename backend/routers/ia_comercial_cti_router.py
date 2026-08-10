from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from services.ia_comercial_agente import gerar_resposta_agente
from services.ia_comercial_cti import IAComercialOpenAIError

router = APIRouter(prefix="/ia-comercial-cti", tags=["IA Comercial CTI"])


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
        "registrado. Use 'maioria' somente quando uma categoria representar estritamente mais de 50% do universo "
        "considerado; em empate ou pluralidade sem maioria absoluta, informe as contagens/percentuais sem chamar "
        "nenhuma categoria de majoritária. Não converta status operacional, administrativo ou documental em venda, "
        "negócio realizado, aceite, entrega ou outro evento comercial sem semântica explícita da fonte que sustente "
        "essa equivalência. Só qualifique cliente como ativo/inativo quando o status correspondente estiver "
        "explicitamente preenchido na fonte consultada. Ao descrever cobertura de campos, use contagens exatas "
        "quando disponíveis: por exemplo, se todos os registros do recorte estão sem modelo, diga que todos estão "
        "sem modelo ou informe X de X, e não 'na maioria dos casos'."
        " REGRA DE EVIDÊNCIA DA EXECUÇÃO ATUAL: o histórico da conversa existe para continuidade semântica, "
        "referências do usuário e compreensão de contexto, mas não é fonte factual operacional da resposta atual. "
        "Toda afirmação factual sobre estado atual ou recorte pesquisado deve ser sustentada por uma fonte "
        "efetivamente consultada nesta execução. Não afirme pipeline, oportunidades ou seus status sem consultar "
        "a fonte de oportunidades nesta execução; não afirme vendas ou vínculos de venda sem consultar vendas; "
        "não nomeie modelos disponíveis do portfólio sem consultar o catálogo; não reutilize números, status, "
        "clientes, modelos ou conclusões de respostas anteriores como se fossem evidência atual. Quando uma fonte "
        "necessária não tiver sido consultada, limite-se ao que as fontes atuais sustentam ou declare que aquele "
        "ponto não foi verificado nesta execução."
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


@router.get("/status")
def status_ia(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return {
        "status": "ready",
        "nome": "IA Comercial CTI",
        "modo": "agente_orquestrador_cti_web",
        "capacidades": [
            "conversa contextual",
            "escolha autônoma de ferramentas CTI",
            "pesquisa web",
            "cruzamento multi-fonte",
            "rastreio auditável",
        ],
        "somente_leitura": True,
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
    mensagem_agente, controle_temporal = _mensagem_com_contexto_temporal(mensagem)
    mensagens_anteriores = _dados(
        supabase.table("cti_ia_mensagens")
        .select("papel,conteudo")
        .eq("conversa_id", conversa_id)
        .order("created_at")
        .limit(40)
        .execute()
    )
    historico = [
        {"role": str(item.get("papel") or "user"), "content": str(item.get("conteudo") or "")}
        for item in mensagens_anteriores
        if item.get("conteudo")
    ]
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

    try:
        resposta_texto, metadados = gerar_resposta_agente(
            mensagem=mensagem_agente,
            historico=historico,
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario,
        )
        metadados["controle_temporal_pergunta"] = controle_temporal
        metadados["controle_temporal_origem"] = "modulo_ia_comercial"
        metadados["controle_recorte_base"] = "restricoes_explicitas_pergunta"
        metadados["controle_proveniencia_evidencia"] = "fonte_explicita"
        metadados["controle_precisao_factual"] = "qualificacoes_exigem_evidencia_explicita"
        metadados["controle_evidencia_execucao"] = "fatos_somente_fontes_consultadas_na_execucao_atual"
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
