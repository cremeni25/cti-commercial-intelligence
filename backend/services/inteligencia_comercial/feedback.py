"""Ajustes da equipe sobre os sinais do agente ("não se aplica" / "adiar").

Cada ajuste esconde um sinal específico (código + entidade) até uma data e
fica gravado com autor e motivo. Assim:

- o vendedor limpa a lista sem apagar nada do CRM;
- o sinal volta sozinho quando o prazo vence (nada é escondido para sempre);
- a gestão enxerga quais alertas a equipe mais dispensa e por quê, e calibra
  os limiares com base em uso real (ver ``resumo_aprendizado``).

A tabela ``cti_inteligencia_feedback`` é opcional: se ainda não existir no
banco, a leitura segue sem supressões e o registro devolve um erro claro.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from .sinais import data, texto

TABELA = "cti_inteligencia_feedback"
DECISOES = {"NAO_SE_APLICA", "ADIAR"}
MOTIVOS = {
    "JA_TRATADO": "Já tratado fora do sistema",
    "CLIENTE_PEDIU_AGUARDAR": "Cliente pediu para aguardar",
    "SERA_ENCERRADO": "Negócio será encerrado",
    "DADO_INCORRETO": "Dado do sistema está incorreto",
    "ALERTA_CEDO_DEMAIS": "Alerta cedo demais para este tipo de venda",
    "OUTRO": "Outro motivo",
}
DIAS_NAO_SE_APLICA = 30
MAX_DIAS_ADIAR = 60


class FeedbackIndisponivel(RuntimeError):
    """A tabela de ajustes ainda não foi criada no banco."""


def _cliente():
    from core.supabase_client import supabase

    return supabase


def prazo_supressao(decisao: str, hoje: date, adiar_ate: date | None) -> date:
    if decisao == "ADIAR":
        limite = hoje + timedelta(days=MAX_DIAS_ADIAR)
        alvo = adiar_ate or hoje + timedelta(days=7)
        return min(max(alvo, hoje + timedelta(days=1)), limite)
    return hoje + timedelta(days=DIAS_NAO_SE_APLICA)


def carregar_feedback(desde: date | None = None) -> list[dict[str, Any]]:
    try:
        consulta = _cliente().table(TABELA).select("*")
        if desde:
            consulta = consulta.gte("created_at", desde.isoformat())
        return consulta.execute().data or []
    except Exception:
        return []


def supressoes_ativas(registros: list[dict[str, Any]], hoje: date) -> set[tuple[str, str, str]]:
    ativas: set[tuple[str, str, str]] = set()
    for item in registros:
        ate = data(item.get("suprimir_ate"))
        if ate and ate >= hoje:
            ativas.add((texto(item.get("codigo")), texto(item.get("entidade_tipo")), texto(item.get("entidade_id"))))
    return ativas


def registrar_feedback(*, usuario_id: str, codigo: str, entidade_tipo: str, entidade_id: str, decisao: str,
                       motivo: str, observacao: str | None, hoje: date, adiar_ate: date | None) -> dict[str, Any]:
    registro = {
        "usuario_id": usuario_id,
        "codigo": codigo,
        "entidade_tipo": entidade_tipo,
        "entidade_id": entidade_id,
        "decisao": decisao,
        "motivo": motivo,
        "observacao": (observacao or "").strip()[:500] or None,
        "suprimir_ate": prazo_supressao(decisao, hoje, adiar_ate).isoformat(),
    }
    try:
        resposta = _cliente().table(TABELA).insert(registro).execute()
    except Exception as erro:
        raise FeedbackIndisponivel(str(erro)) from erro
    dados = getattr(resposta, "data", None) or [registro]
    return dados[0]


def resumo_aprendizado(registros: list[dict[str, Any]]) -> dict[str, Any]:
    """O que a equipe mais dispensa — base para calibrar regras e limiares."""
    por_codigo: dict[str, Counter] = defaultdict(Counter)
    for item in registros:
        por_codigo[texto(item.get("codigo"))][texto(item.get("motivo")) or "OUTRO"] += 1
    sinais = [
        {
            "codigo": codigo,
            "total": sum(motivos.values()),
            "motivos": [{"motivo": m, "rotulo": MOTIVOS.get(m, m), "quantidade": q} for m, q in motivos.most_common()],
        }
        for codigo, motivos in por_codigo.items()
    ]
    sinais.sort(key=lambda item: item["total"], reverse=True)
    return {"total_ajustes": len(registros), "sinais": sinais}
