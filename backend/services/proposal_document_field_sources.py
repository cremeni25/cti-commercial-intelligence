from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from services.proposal_document_definitions import DOCUMENT_DEFINITIONS


class FieldAvailability(StrEnum):
    EXISTS = "JA_EXISTE"
    CREATE = "PRECISA_SER_CRIADO"
    OTHER_TABLE = "VEM_DE_OUTRA_TABELA"


@dataclass(frozen=True)
class ProposalFieldSource:
    field_code: str
    availability: FieldAvailability
    table: str
    column: str
    fallback_columns: tuple[str, ...] = ()
    derived: bool = False


def _source(
    document: str,
    field: str,
    availability: FieldAvailability,
    table: str,
    column: str,
    *fallback_columns: str,
    derived: bool = False,
) -> ProposalFieldSource:
    return ProposalFieldSource(
        field_code=f"{document.lower()}.{field}",
        availability=availability,
        table=table,
        column=column,
        fallback_columns=tuple(fallback_columns),
        derived=derived,
    )


def _independent_document_sources(document: str, *, voltage: bool, lynx_months: bool) -> tuple[ProposalFieldSource, ...]:
    """Cria uma classificação exclusiva para um documento, sem herança entre documentos."""
    sources = [
        _source(document, "data", FieldAvailability.EXISTS, "cti_propostas", "emitida_em", "created_at"),
        _source(document, "cliente_nome", FieldAvailability.OTHER_TABLE, "clientes", "razao_social", "nome_fantasia", "nome"),
        _source(document, "cliente_cpf_cnpj", FieldAvailability.OTHER_TABLE, "clientes", "cpf_cnpj", "cnpj", "cpf"),
        _source(document, "cliente_inscricao_estadual", FieldAvailability.OTHER_TABLE, "clientes", "inscricao_estadual", "ie"),
        _source(document, "cliente_endereco_completo", FieldAvailability.OTHER_TABLE, "clientes", "endereco_completo", "endereco"),
        _source(document, "cliente_telefones", FieldAvailability.OTHER_TABLE, "clientes", "telefone", "celular", "whatsapp"),
        _source(document, "cliente_email", FieldAvailability.OTHER_TABLE, "clientes", "email", "email_principal"),
        _source(document, "quantidade_texto", FieldAvailability.EXISTS, "cti_oportunidade_itens", "quantidade", derived=True),
        _source(document, "quantidade", FieldAvailability.EXISTS, "cti_oportunidade_itens", "quantidade"),
        _source(document, "valor_unitario", FieldAvailability.EXISTS, "cti_oportunidade_itens", "preco_unitario"),
        _source(document, "valor_total", FieldAvailability.EXISTS, "cti_oportunidade_itens", "valor_total", derived=True),
        _source(document, "acessorios_itens_complementares", FieldAvailability.EXISTS, "cti_oportunidade_itens", "opcionais"),
        _source(document, "condicoes_pagamento", FieldAvailability.EXISTS, "cti_oportunidade_itens", "condicao_pagamento"),
        _source(document, "valor_entrada", FieldAvailability.CREATE, "cti_oportunidade_itens", "valor_entrada"),
        _source(document, "autorizada_nome_endereco", FieldAvailability.CREATE, "cti_oportunidade_itens", "autorizada_nome_endereco"),
    ]
    if voltage:
        sources.insert(8, _source(document, "voltagem", FieldAvailability.CREATE, "cti_oportunidade_itens", "voltagem"))
    if lynx_months:
        sources.append(_source(document, "lynx_periodo_meses", FieldAvailability.CREATE, "cti_oportunidade_itens", "lynx_meses"))
    return tuple(sources)


# Cada chamada materializa um conjunto novo e exclusivo. Nenhum documento herda campos de outro.
DOCUMENT_FIELD_SOURCES: dict[str, tuple[ProposalFieldSource, ...]] = {
    "CITIMAX_280": _independent_document_sources("CITIMAX_280", voltage=True, lynx_months=False),
    "CITIMAX_400": _independent_document_sources("CITIMAX_400", voltage=True, lynx_months=False),
    "CITIMAX_500": _independent_document_sources("CITIMAX_500", voltage=True, lynx_months=False),
    "CITIMAX_D6": _independent_document_sources("CITIMAX_D6", voltage=True, lynx_months=False),
    "CITIMAX_D7": _independent_document_sources("CITIMAX_D7", voltage=True, lynx_months=False),
    "S8": _independent_document_sources("S8", voltage=False, lynx_months=False),
    "S9": _independent_document_sources("S9", voltage=False, lynx_months=False),
    "SUPRA_750": _independent_document_sources("SUPRA_750", voltage=False, lynx_months=False),
    "SUPRA_850": _independent_document_sources("SUPRA_850", voltage=False, lynx_months=False),
    "SUPRA_1150": _independent_document_sources("SUPRA_1150", voltage=False, lynx_months=False),
    "VECTOR_8500": _independent_document_sources("VECTOR_8500", voltage=False, lynx_months=True),
    "VECTOR_HE19": _independent_document_sources("VECTOR_HE19", voltage=False, lynx_months=True),
    "X4_7500": _independent_document_sources("X4_7500", voltage=False, lynx_months=True),
    "X4_7700": _independent_document_sources("X4_7700", voltage=False, lynx_months=True),
    "XARIOS_350": _independent_document_sources("XARIOS_350", voltage=True, lynx_months=False),
    "XARIOS_6": _independent_document_sources("XARIOS_6", voltage=True, lynx_months=False),
}


def validate_document_field_sources() -> None:
    definition_codes = {definition.code for definition in DOCUMENT_DEFINITIONS}
    source_codes = set(DOCUMENT_FIELD_SOURCES)
    if definition_codes != source_codes:
        missing = sorted(definition_codes - source_codes)
        extra = sorted(source_codes - definition_codes)
        raise RuntimeError(f"Classificação documental incompleta. Ausentes={missing}; extras={extra}")

    for definition in DOCUMENT_DEFINITIONS:
        expected = {field.code for field in definition.fields}
        classified = {source.field_code for source in DOCUMENT_FIELD_SOURCES[definition.code]}
        if expected != classified:
            missing = sorted(expected - classified)
            extra = sorted(classified - expected)
            raise RuntimeError(
                f"Classificação divergente para {definition.code}. Ausentes={missing}; extras={extra}"
            )


validate_document_field_sources()
