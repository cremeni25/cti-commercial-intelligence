"""Resumo diário no celular (Web Push) a partir do Agente de Inteligência.

Fluxo:
1. No app, a pessoa ativa o resumo; o navegador gera uma assinatura push
   (endpoint + chaves) que guardamos em ``cti_push_assinaturas``.
2. Um agendamento chama ``enviar_resumo_diario`` nos dias úteis de manhã.
3. Para cada usuário inscrito e ATIVO, o perfil e as permissões são relidos
   agora (nunca confiamos no perfil do dia da inscrição), a leitura do agente é
   montada no escopo dele e enviamos a manchete + a primeira prioridade.

Regras de respeito ao usuário:
- sem prioridades, sem notificação (nada de "bom dia" vazio);
- uma notificação por dia por usuário (tag fixa substitui a anterior);
- assinatura recusada pelo navegador (404/410) é desativada sozinha;
- a mensagem aparece na tela bloqueada: leva só o título da primeira
  prioridade (o que fazer e com qual cliente), nunca valores em reais — o
  detalhe só aparece dentro do app autenticado.

Zero configuração manual:
- o par de chaves VAPID é gerado na primeira utilização e guardado no cofre
  privado do agente (``config/vapid.json``); ``VAPID_PUBLIC_KEY`` e
  ``VAPID_PRIVATE_KEY`` no ambiente, se existirem, têm precedência;
- inscrições ficam em ``push/<usuario_id>.json`` no mesmo cofre;
- uma marca ``envios/resumo-diario-<data>.json`` garante um único envio por dia,
  mesmo que o agendamento repita a chamada.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Any, Callable

from services import cofre_agente as cofre

PASTA_ASSINATURAS = "push"
DOC_CHAVES = "config/vapid.json"
URL_DESTINO = "/crm-app/prioridades"
TAG_RESUMO = "cti-resumo-diario"
SUBJECT_PADRAO = "https://app.cti-intelligence.com"
_CHAVES_CACHE: dict[str, str] | None = None


class PushIndisponivel(RuntimeError):
    """Cofre do agente indisponível: o recurso fica desligado com aviso."""


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def gerar_par_vapid() -> dict[str, str]:
    import base64

    from cryptography.hazmat.primitives import serialization
    from py_vapid import Vapid

    vapid = Vapid()
    vapid.generate_keys()
    b64 = lambda bruto: base64.urlsafe_b64encode(bruto).rstrip(b"=").decode()
    publica = vapid.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    privada = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
    return {"publica": b64(publica), "privada": b64(privada), "criada_em": _agora()}


def chaves_vapid() -> dict[str, str]:
    """Ambiente tem precedência; senão, cofre; senão, gera e guarda (uma vez)."""
    global _CHAVES_CACHE
    publica_env, privada_env = os.getenv("VAPID_PUBLIC_KEY", "").strip(), os.getenv("VAPID_PRIVATE_KEY", "").strip()
    if publica_env and privada_env:
        return {"publica": publica_env, "privada": privada_env}
    if _CHAVES_CACHE:
        return _CHAVES_CACHE
    try:
        chaves = cofre.ler(DOC_CHAVES)
        if not (isinstance(chaves, dict) and chaves.get("publica") and chaves.get("privada")):
            novas = gerar_par_vapid()
            # Criação exclusiva: se outra instância gerou ao mesmo tempo, vale a dela.
            chaves = novas if cofre.criar_exclusivo(DOC_CHAVES, novas) else cofre.ler(DOC_CHAVES)
    except Exception as erro:
        raise PushIndisponivel(str(erro)) from erro
    if not (isinstance(chaves, dict) and chaves.get("publica") and chaves.get("privada")):
        raise PushIndisponivel("Chaves do push indisponíveis.")
    _CHAVES_CACHE = {"publica": chaves["publica"], "privada": chaves["privada"]}
    return _CHAVES_CACHE


def chave_publica() -> str:
    try:
        return chaves_vapid()["publica"]
    except PushIndisponivel:
        return ""


def push_configurado() -> bool:
    return bool(chave_publica())


def validar_assinatura(assinatura: dict[str, Any]) -> dict[str, str]:
    endpoint = str(assinatura.get("endpoint") or "").strip()
    chaves = assinatura.get("keys") if isinstance(assinatura.get("keys"), dict) else {}
    p256dh = str(chaves.get("p256dh") or "").strip()
    auth = str(chaves.get("auth") or "").strip()
    if not endpoint.startswith("https://") or len(endpoint) > 1000 or not p256dh or not auth:
        raise ValueError("Assinatura de notificação inválida.")
    return {"endpoint": endpoint, "p256dh": p256dh, "auth": auth}


def _doc_usuario(usuario_id: str) -> str:
    return cofre.caminho(PASTA_ASSINATURAS, f"{usuario_id}.json")


def _todas_por_usuario() -> dict[str, list[dict[str, Any]]]:
    try:
        documentos = cofre.ler_pasta(PASTA_ASSINATURAS)
    except Exception as erro:
        raise PushIndisponivel(str(erro)) from erro
    return {nome[:-5]: [a for a in (lista or []) if isinstance(a, dict)] for nome, lista in documentos.items()}


def salvar_assinatura(usuario_id: str, assinatura: dict[str, Any], user_agent: str = "") -> dict[str, Any]:
    dados = validar_assinatura(assinatura)
    registro = {**dados, "usuario_id": str(usuario_id), "user_agent": (user_agent or "")[:300], "ativo": True, "falhas": 0, "updated_at": _agora()}
    try:
        todas = _todas_por_usuario()
        # Mesmo aparelho com outra pessoa logada: a inscrição muda de dono, para
        # que ninguém receba as prioridades de outro vendedor.
        for outro, lista in todas.items():
            if outro != str(usuario_id) and any(a.get("endpoint") == dados["endpoint"] for a in lista):
                cofre.gravar(_doc_usuario(outro), [a for a in lista if a.get("endpoint") != dados["endpoint"]])
        proprias = [a for a in todas.get(str(usuario_id), []) if a.get("endpoint") != dados["endpoint"]]
        cofre.gravar(_doc_usuario(str(usuario_id)), [*proprias, registro])
    except PushIndisponivel:
        raise
    except Exception as erro:
        raise PushIndisponivel(str(erro)) from erro
    return {"endpoint": dados["endpoint"], "ativo": True}


def remover_assinatura(usuario_id: str, endpoint: str) -> None:
    try:
        caminho_doc = _doc_usuario(str(usuario_id))
        lista = cofre.ler(caminho_doc, []) or []
        cofre.gravar(caminho_doc, [{**a, "ativo": False, "updated_at": _agora()} if a.get("endpoint") == endpoint else a for a in lista if isinstance(a, dict)])
    except Exception as erro:
        raise PushIndisponivel(str(erro)) from erro


def assinaturas_ativas(usuario_id: str | None = None) -> list[dict[str, Any]]:
    todas = _todas_por_usuario()
    saida = []
    for dono, lista in todas.items():
        if usuario_id and dono != str(usuario_id):
            continue
        saida.extend({**a, "usuario_id": dono} for a in lista if a.get("ativo") is not False)
    return saida


def mensagem_do_briefing(briefing: dict[str, Any]) -> dict[str, Any] | None:
    prioridades = briefing.get("prioridades") or []
    if not prioridades:
        return None
    primeira = prioridades[0]
    quantidade = len(prioridades)
    # A notificação aparece na tela bloqueada: sem valores em reais nem manchete
    # financeira — só o que fazer primeiro. O detalhe fica dentro do app.
    corpo = f"Comece por: {str(primeira.get('titulo') or '').strip()}".strip()
    if len(corpo) > 170:
        corpo = corpo[:167].rstrip() + "..."
    return {
        "title": f"Seu dia comercial · {quantidade} prioridade{'s' if quantidade != 1 else ''}",
        "body": corpo if corpo != "Comece por:" else "Abra o CTI para ver suas prioridades.",
        "url": URL_DESTINO,
        "tag": TAG_RESUMO,
    }


def _enviar_push(assinatura: dict[str, Any], mensagem: dict[str, Any]) -> None:
    from pywebpush import webpush  # import tardio: só quem envia paga o custo

    webpush(
        subscription_info={"endpoint": assinatura["endpoint"], "keys": {"p256dh": assinatura["p256dh"], "auth": assinatura["auth"]}},
        data=json.dumps(mensagem, ensure_ascii=False),
        vapid_private_key=chaves_vapid()["privada"],
        vapid_claims={"sub": os.getenv("VAPID_SUBJECT", "").strip() or SUBJECT_PADRAO},
        ttl=6 * 60 * 60,  # se o celular estiver offline, vale até o fim da manhã
    )


def _status_resposta(erro: Exception) -> int | None:
    resposta = getattr(erro, "response", None)
    return getattr(resposta, "status_code", None)


def enviar_para_assinaturas(assinaturas: list[dict[str, Any]], mensagem: dict[str, Any], enviar: Callable[[dict, dict], None] | None = None) -> dict[str, int]:
    enviar = enviar or _enviar_push
    resultado = {"enviadas": 0, "falhas": 0, "desativadas": 0}
    atualizacoes: dict[str, dict[str, Any]] = {}
    for assinatura in assinaturas:
        try:
            enviar(assinatura, mensagem)
            resultado["enviadas"] += 1
            atualizacoes[assinatura["endpoint"]] = {"ultimo_envio_em": _agora(), "falhas": 0}
        except Exception as erro:
            status = _status_resposta(erro)
            expirada = status in (404, 410)
            resultado["desativadas" if expirada else "falhas"] += 1
            falhas = int(assinatura.get("falhas") or 0) + 1
            atualizacoes[assinatura["endpoint"]] = {"falhas": falhas, "ativo": not expirada and falhas < 5}
    donos = {str(a.get("usuario_id")) for a in assinaturas if a.get("usuario_id")}
    for dono in donos:
        try:  # o registro de entrega nunca interrompe o envio aos demais
            caminho_doc = _doc_usuario(dono)
            lista = cofre.ler(caminho_doc, []) or []
            cofre.gravar(caminho_doc, [{**a, **atualizacoes.get(a.get("endpoint"), {}), "updated_at": _agora()} if a.get("endpoint") in atualizacoes else a for a in lista if isinstance(a, dict)])
        except Exception:
            pass
    return resultado


def _perfis_ativos(ids: set[str]) -> dict[str, dict[str, Any]]:
    from core.admin_auth import _buscar_permissoes, _normalizar_perfil

    perfis: dict[str, dict[str, Any]] = {}
    from core.supabase_client import supabase

    linhas = supabase.table("cti_users").select("*").execute().data or []
    for linha in linhas:
        usuario_id = str(linha.get("id") or "")
        if usuario_id not in ids:
            continue
        if linha.get("ativo") is False or str(linha.get("status_acesso") or "").upper() in {"INATIVO", "BLOQUEADO", "REJEITADO"}:
            continue
        tipo = _normalizar_perfil(linha)
        if not tipo or tipo in {"AUTORIZADO_CARRIER", "GESTOR_AUTORIZADO_CARRIER", "CARRIER_MASTER"}:
            continue
        perfis[usuario_id] = {"tipo_usuario": tipo, "permissoes": _buscar_permissoes(usuario_id, tipo)}
    return perfis


def _consolidado(perfil: dict[str, Any]) -> bool:
    return perfil["tipo_usuario"] == "ADMIN_MASTER" or (perfil["tipo_usuario"] == "DIRETOR_VIENA_SP" and bool(perfil["permissoes"].get("acesso_total")))


def enviar_resumo_diario(*, hoje: date | None = None, enviar: Callable[[dict, dict], None] | None = None, forcar: bool = False) -> dict[str, Any]:
    from services.inteligencia_comercial import filtrar_escopo, montar_briefing
    from services.inteligencia_comercial import servico
    from services.inteligencia_comercial.briefing import hoje_operacional
    from services.inteligencia_comercial.feedback import supressoes_ativas

    hoje = hoje or hoje_operacional()
    if enviar is None:
        chaves_vapid()  # garante as chaves antes de qualquer envio
    if not forcar:
        try:
            primeira_vez = cofre.criar_exclusivo(cofre.caminho("envios", f"resumo-diario-{hoje.isoformat()}.json"), {"iniciado_em": _agora()})
        except Exception as erro:
            raise PushIndisponivel(str(erro)) from erro
        if not primeira_vez:
            return {"data": hoje.isoformat(), "ja_enviado": True}
    assinaturas = assinaturas_ativas()
    por_usuario: dict[str, list[dict[str, Any]]] = {}
    for assinatura in assinaturas:
        por_usuario.setdefault(str(assinatura.get("usuario_id")), []).append(assinatura)
    relatorio = {"data": hoje.isoformat(), "ja_enviado": False, "usuarios": len(por_usuario), "notificados": 0, "sem_prioridades": 0, "ignorados": 0, "enviadas": 0, "falhas": 0, "desativadas": 0}
    if not por_usuario:
        return relatorio

    perfis = _perfis_ativos(set(por_usuario))
    # Fontes lidas uma única vez para todos os usuários.
    oportunidades = servico._carregar_oportunidades()
    try:
        atividades = servico._carregar_atividades()
    except Exception:
        atividades = []
    supressoes = supressoes_ativas(servico._carregar_feedback(hoje), hoje)

    for usuario_id, assinaturas_usuario in por_usuario.items():
        perfil = perfis.get(usuario_id)
        if not perfil:
            relatorio["ignorados"] += 1  # inativo, externo ou inexistente
            continue
        filtro = None if _consolidado(perfil) else usuario_id
        proprias, atividades_proprias = filtrar_escopo(oportunidades, atividades, filtro)
        briefing = montar_briefing(proprias, atividades_proprias, hoje=hoje, supressoes=supressoes, limite_prioridades=10)
        mensagem = mensagem_do_briefing(briefing)
        if not mensagem:
            relatorio["sem_prioridades"] += 1
            continue
        resultado = enviar_para_assinaturas(assinaturas_usuario, mensagem, enviar)
        relatorio["notificados"] += 1 if resultado["enviadas"] else 0
        for chave in ("enviadas", "falhas", "desativadas"):
            relatorio[chave] += resultado[chave]
    return relatorio
