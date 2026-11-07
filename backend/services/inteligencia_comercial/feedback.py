"""Ajustes da equipe sobre os sinais do agente ("não se aplica" / "adiar").

Cada ajuste esconde um sinal específico (código + entidade) até uma data e
fica gravado com autor e motivo. Assim:

- o vendedor limpa a lista sem apagar nada do CRM;
- o sinal volta sozinho quando o prazo vence (nada é escondido para sempre);
- a gestão enxerga quais alertas a equipe mais dispensa e por quê, e calibra
  os limiares com base em uso real (ver ``resumo_aprendizado``).

Armazenamento: cofre do agente (``services/cofre_agente``), um documento por
usuário em ``feedback/<usuario_id>.json`` — criado automaticamente, sem
migração. Registros com mais de ``RETENCAO_DIAS`` são expurgados na gravação.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from services import cofre_agente as cofre

from .sinais import data, texto

PASTA = "feedback"
RETENCAO_DIAS = 180
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
    """O cofre do agente não respondeu."""


def prazo_supressao(decisao: str, hoje: date, adiar_ate: date | None) -> date:
    if decisao == "ADIAR":
        limite = hoje + timedelta(days=MAX_DIAS_ADIAR)
        alvo = adiar_ate or hoje + timedelta(days=7)
        return min(max(alvo, hoje + timedelta(days=1)), limite)
    return hoje + timedelta(days=DIAS_NAO_SE_APLICA)


def carregar_feedback(desde: date | None = None) -> list[dict[str, Any]]:
    try:
        documentos = cofre.ler_pasta(PASTA)
    except Exception:
        return []  # leitura derivada: sem cofre, a leitura segue sem supressões
    registros = [r for lista in documentos.values() if isinstance(lista, list) for r in lista if isinstance(r, dict)]
    if desde:
        registros = [r for r in registros if (data(r.get("created_at")) or date.max) >= desde]
    return registros


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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        caminho_doc = cofre.caminho(PASTA, f"{usuario_id}.json")
        atuais = cofre.ler(caminho_doc, []) or []
        limite = (hoje - timedelta(days=RETENCAO_DIAS)).isoformat()
        mantidos = [r for r in atuais if isinstance(r, dict) and str(r.get("created_at") or "")[:10] >= limite]
        cofre.gravar(caminho_doc, [*mantidos, registro])
    except Exception as erro:
        raise FeedbackIndisponivel(str(erro)) from erro
    return registro


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
