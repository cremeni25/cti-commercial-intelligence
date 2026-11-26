"""Tela "Hoje": de 3 a 5 cartões do que cada pessoa deve fazer agora.

Não cria regra nova: junta o que o CTI já calcula.
- Negócios: as prioridades da Central de Inteligência (mesmo escopo e mesmos ajustes da equipe).
- Carteira: o cliente mais importante para abordar (janela de renovação sem negócio aberto,
  depois cliente inativo recorrente, depois prospect com frota grande).
- Master: comissões de indicadores com nota fiscal esperando pagamento.

Cada fonte é lida de forma independente: se uma falhar, os demais cartões continuam.
"""
from __future__ import annotations

from typing import Any

LIMITE = 5


def _cartao_prioridade(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "tipo": "negocio" if p.get("categoria") != "acao" else "agenda",
        "titulo": p.get("titulo") or "Prioridade comercial",
        "detalhe": p.get("explicacao") or "",
        "acao": p.get("acao_recomendada") or "Abrir",
        "cliente": p.get("cliente_nome") or None,
        "valor": p.get("valor") or 0,
        "href": p.get("rota") or "/central",
        "href_app": p.get("rota_app") or p.get("rota") or "/crm-app",
        "tom": "risco" if p.get("categoria") == "risco" else ("oportunidade" if p.get("categoria") == "oportunidade" else "acao"),
    }


def _cartao_carteira(responsavel_id: str | None) -> dict[str, Any] | None:
    from services import carteira_setorizada as carteira

    perfis, _, _ = carteira._carteira_completa()
    base = [p for p in perfis if responsavel_id is None or p["responsavel_id"] == responsavel_id]
    regras = [
        ("Ofereça a renovação", lambda p: "JANELA_RENOVACAO" in p["sinais"] and not p["negocios_abertos"],
         lambda p: f"Frota com equipamentos de 6 anos ou mais ({p['frota_registrada']} registrados) e nenhum negócio aberto."),
        ("Reative este cliente", lambda p: p["grupo"] == "CLIENTE_INATIVO" and "RECORRENTE" in p["sinais"] and not p["negocios_abertos"],
         lambda p: f"Já comprou da Viena ({p['compras']} compras) e não compra desde {p['ultima_compra'] or 'há mais de 24 meses'}."),
        ("Apresente a Carrier", lambda p: p["grupo"] == "PROSPECT_COM_FROTA" and p["porte"] in {"GRANDE", "MEDIO"} and not p["negocios_abertos"],
         lambda p: f"Frota registrada de {p['frota_registrada']}, sendo {p['frota_concorrencia']} da concorrência, e ainda não comprou da Viena."),
    ]
    for acao, regra, detalhe in regras:
        candidatos = sorted((p for p in base if regra(p)), key=carteira._prioridade)
        if candidatos:
            p = candidatos[0]
            mais = len(candidatos) - 1
            return {
                "tipo": "carteira", "titulo": f"{acao}: {p['nome']}",
                "detalhe": detalhe(p) + (f" Outros {mais} na mesma situação." if mais else ""),
                "acao": "Abrir a ficha da empresa", "cliente": p["nome"], "valor": 0,
                "href": f"/carteira?empresa={p['cliente_id']}", "href_app": f"/carteira?empresa={p['cliente_id']}", "tom": "oportunidade",
            }
    return None


def _cartao_comissoes() -> dict[str, Any] | None:
    from services import indicacoes_comerciais as ind

    ind.sincronizar_com_oportunidades()
    vendidas = [i for i in ind.listar_indicacoes(status="VENDIDA")]
    com_nf = [i for i in vendidas if i.get("comissao_status") == "NF_RECEBIDA"]
    sem_nf = [i for i in vendidas if i.get("comissao_status") == "A_PAGAR"]
    if not com_nf and not sem_nf:
        return None
    moeda = lambda v: f"R$ {v:,.0f}".replace(",", ".")  # noqa: E731
    if com_nf:
        total = sum(float(i.get("comissao_valor") or 0) for i in com_nf)
        titulo, acao = (f"Pagar {len(com_nf)} {'comissões' if len(com_nf) > 1 else 'comissão'} com nota fiscal: {moeda(total)}"), "Abrir indicações"
        detalhe = f"Outras {len(sem_nf)} aguardam a nota fiscal do indicador." if sem_nf else "Nenhuma outra comissão pendente."
    else:
        total = sum(float(i.get("comissao_valor") or 0) for i in sem_nf)
        titulo, acao = (f"{len(sem_nf)} {'comissões aguardam' if len(sem_nf) > 1 else 'comissão aguarda'} nota fiscal: {moeda(total)}"), "Abrir indicações"
        detalhe = "Cobre a nota fiscal dos indicadores para liberar o pagamento."
    return {"tipo": "comissao", "titulo": titulo, "detalhe": detalhe, "acao": acao, "cliente": None, "valor": total,
            "href": "/indicadores", "href_app": "/indicadores", "tom": "acao"}


def montar(usuario_id: str, consolidado: bool, master: bool, pode_comercial: bool) -> dict[str, Any]:
    cartoes: list[dict[str, Any]] = []
    limitacoes: list[str] = []
    manchete = ""
    escopo = None if consolidado else usuario_id

    if master:
        try:
            cartao = _cartao_comissoes()
            if cartao:
                cartoes.append(cartao)
        except Exception:
            limitacoes.append("Comissões de indicadores indisponíveis nesta leitura.")

    prioridades: list[dict[str, Any]] = []
    if pode_comercial:
        try:
            from services.inteligencia_comercial import gerar_briefing

            briefing = gerar_briefing(usuario_id=usuario_id, consolidado=consolidado, limite_prioridades=LIMITE)
            manchete = briefing.get("manchete") or ""
            prioridades = briefing.get("prioridades") or []
        except Exception:
            limitacoes.append("Prioridades de negócios indisponíveis nesta leitura.")
        try:
            carteira = _cartao_carteira(escopo)
        except Exception:
            carteira = None
            limitacoes.append("Carteira indisponível nesta leitura.")
    else:
        carteira = None

    # Até 3 negócios, um cartão de carteira e o restante com mais negócios, sempre no máximo 5.
    vagas_negocio = LIMITE - len(cartoes) - (1 if carteira else 0)
    cartoes.extend(_cartao_prioridade(p) for p in prioridades[:max(vagas_negocio, 0)])
    if carteira and len(cartoes) < LIMITE:
        cartoes.append(carteira)
    return {
        "manchete": manchete or ("Tudo em dia por aqui." if not cartoes else ""),
        "cartoes": cartoes[:LIMITE],
        "limitacoes": limitacoes,
    }
