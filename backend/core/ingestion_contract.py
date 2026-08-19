from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PIPELINE_CANONICO = (
    "RECEBIMENTO",
    "IDENTIFICACAO",
    "NORMALIZACAO",
    "VALIDACAO",
    "CLASSIFICACAO",
    "PERSISTENCIA",
    "ANALYTICS",
    "IA",
    "DASHBOARD",
)

ENTRADAS_CANONICAS = {"UPLOAD_OPERACIONAL", "BACKOFFICE_FONTES"}


@dataclass(frozen=True)
class ContratoIngestao:
    entrada: str
    arquivo: str
    contexto: str
    destino_inicial: str
    persistencia_operacional_automatica: bool
    governanca_master: bool

    def serializar(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["pipeline_canonico"] = list(PIPELINE_CANONICO)
        payload["nucleo"] = "CTI_INGESTAO_CANONICA"
        payload["versao_contrato"] = "1.0"
        return payload


def contrato_upload_operacional(arquivo: str, contexto: str = "viena_sp") -> dict[str, Any]:
    return ContratoIngestao(
        entrada="UPLOAD_OPERACIONAL",
        arquivo=arquivo,
        contexto=contexto,
        destino_inicial="DOMINIO_OPERACIONAL_VALIDADO",
        persistencia_operacional_automatica=True,
        governanca_master=False,
    ).serializar()


def contrato_backoffice_fontes(arquivo: str, contexto: str = "cti_web") -> dict[str, Any]:
    return ContratoIngestao(
        entrada="BACKOFFICE_FONTES",
        arquivo=arquivo,
        contexto=contexto,
        destino_inicial="STAGING_GOVERNADO_DE_FONTES",
        persistencia_operacional_automatica=False,
        governanca_master=True,
    ).serializar()


def validar_contrato(payload: dict[str, Any]) -> bool:
    return (
        payload.get("nucleo") == "CTI_INGESTAO_CANONICA"
        and payload.get("entrada") in ENTRADAS_CANONICAS
        and payload.get("pipeline_canonico") == list(PIPELINE_CANONICO)
    )
