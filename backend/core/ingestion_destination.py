from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CLASSIFICACOES_OPERACIONAIS = {
    "COMERCIAL",
    "MERCADO_ANFIR",
    "TERRITORIAL",
    "FINANCEIRO",
}

CLASSIFICACOES_CONHECIMENTO = {
    "TECNICO_PRODUTO",
    "CONTRATUAL_DOCUMENTAL",
    "DOCUMENTAL_VISUAL",
    "DOCUMENTAL_GERAL",
}


@dataclass(frozen=True)
class DecisaoDestino:
    classificacao: str
    confianca: float
    destino: str
    promocao_operacional_automatica: bool
    exige_validacao: bool
    consumivel_ia: bool
    consumivel_dashboard: bool
    motivo: str

    def serializar(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["regra"] = "CTI_DESTINO_CANONICO_V1"
        return payload


def decidir_destino(
    classificacao: str | None,
    confianca: float | int | None,
    *,
    entrada: str = "BACKOFFICE_FONTES",
    possui_registros_semanticos: bool = True,
) -> dict[str, Any]:
    classe = str(classificacao or "DOCUMENTAL_GERAL").strip().upper()
    try:
        conf = float(confianca or 0)
    except (TypeError, ValueError):
        conf = 0.0

    if not possui_registros_semanticos:
        return DecisaoDestino(
            classificacao=classe,
            confianca=conf,
            destino="STAGING_GOVERNADO",
            promocao_operacional_automatica=False,
            exige_validacao=True,
            consumivel_ia=False,
            consumivel_dashboard=False,
            motivo="Conteúdo sem registros semânticos suficientes para consumo.",
        ).serializar()

    if entrada == "UPLOAD_OPERACIONAL":
        return DecisaoDestino(
            classificacao=classe,
            confianca=conf,
            destino="DOMINIO_OPERACIONAL_VALIDADO",
            promocao_operacional_automatica=True,
            exige_validacao=False,
            consumivel_ia=True,
            consumivel_dashboard=True,
            motivo="Entrada operacional já passou pelo parser e validação específicos do domínio.",
        ).serializar()

    if classe in CLASSIFICACOES_OPERACIONAIS:
        return DecisaoDestino(
            classificacao=classe,
            confianca=conf,
            destino="CANDIDATO_OPERACIONAL_VALIDACAO",
            promocao_operacional_automatica=False,
            exige_validacao=True,
            consumivel_ia=True,
            consumivel_dashboard=False,
            motivo="Conteúdo potencialmente operacional; exige reconciliação e validação antes de promover ao núcleo de negócio.",
        ).serializar()

    if classe in CLASSIFICACOES_CONHECIMENTO:
        return DecisaoDestino(
            classificacao=classe,
            confianca=conf,
            destino="CONHECIMENTO_SEMANTICO",
            promocao_operacional_automatica=False,
            exige_validacao=False,
            consumivel_ia=True,
            consumivel_dashboard=False,
            motivo="Conteúdo de conhecimento; pode enriquecer IA sem criar verdade operacional.",
        ).serializar()

    return DecisaoDestino(
        classificacao=classe,
        confianca=conf,
        destino="STAGING_GOVERNADO",
        promocao_operacional_automatica=False,
        exige_validacao=True,
        consumivel_ia=False,
        consumivel_dashboard=False,
        motivo="Classificação não reconhecida para promoção; permanece governada até revisão.",
    ).serializar()
