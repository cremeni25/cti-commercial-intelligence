from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping
from zipfile import ZIP_DEFLATED, ZipFile

from services.proposal_template_catalog import ProposalTemplateDefinition, template_for_equipment


class OfficialProposalDocumentError(ValueError):
    """Raised when an official Carrier proposal cannot be generated safely."""


@dataclass(frozen=True)
class GeneratedOfficialDocument:
    filename: str
    content: bytes
    sha256: str
    template_code: str
    template_version: int
    source_sha256: str


# Anchors are intentionally limited to fields that already exist in the official files.
# The engine replaces text only; drawings, media, relationships, headers, footers,
# tables, section properties and page breaks remain untouched inside the DOCX package.
FIELD_ANCHORS: dict[str, tuple[str, ...]] = {
    "data": ("Data:",),
    "cliente_nome": ("Nome do cliente:",),
    "cpf_cnpj": ("CPF/CNPJ:",),
    "inscricao_estadual": ("INSC:",),
    "endereco_completo": ("Endereço Completo:",),
    "telefones": ("Telefones de contato:",),
    "email": ("E-mail:",),
    "voltagem": ("Voltagem:",),
    "quantidade": ("Quantidade:",),
    "valor_unitario": ("Valor unitário desta proposta:",),
    "valor_total": ("Valor Total desta proposta:",),
    "acessorios": ("Acessórios / Itens Complementares:",),
    "condicoes_pagamento": ("Condições de pagamentos:",),
    "valor_entrada": ("Valor:",),
    "autorizada": ("Nome e endereço da Autorizada:",),
    "validade": ("Validade da proposta:",),
}


REQUIRED_DOCUMENT_FIELDS = {
    "cliente_nome",
    "cpf_cnpj",
    "endereco_completo",
    "telefones",
    "email",
    "quantidade",
    "valor_unitario",
    "valor_total",
    "condicoes_pagamento",
    "validade",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def validate_document_payload(payload: Mapping[str, Any]) -> None:
    missing = sorted(key for key in REQUIRED_DOCUMENT_FIELDS if not _clean(payload.get(key)))
    if missing:
        raise OfficialProposalDocumentError(
            "Dados obrigatórios ausentes para emissão do documento oficial: " + ", ".join(missing)
        )


def _replace_anchor_text(xml: str, anchor: str, value: str) -> tuple[str, bool]:
    """Append a field value to the exact official anchor without changing package layout.

    Word can split visible text across multiple runs. The first implementation accepts
    only contiguous anchors and fails closed when an anchor is not found; it never
    recreates or approximates the official proposal.
    """
    escaped_value = (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    marker = anchor
    position = xml.find(marker)
    if position < 0:
        return xml, False
    end_text = xml.find("</w:t>", position)
    if end_text < 0:
        return xml, False
    insert_at = end_text
    return xml[:insert_at] + " " + escaped_value + xml[insert_at:], True


def render_official_docx(
    source: bytes,
    equipment: str,
    payload: Mapping[str, Any],
    *,
    output_number: str,
) -> GeneratedOfficialDocument:
    template = template_for_equipment(equipment)
    if not template.source_filename.lower().endswith(".docx"):
        raise OfficialProposalDocumentError(
            f"O modelo {template.equipment} está em formato DOC legado e precisa ser convertido para DOCX "
            "sem alteração visual antes da emissão automatizada."
        )
    validate_document_payload(payload)
    source_hash = sha256(source).hexdigest()

    input_buffer = BytesIO(source)
    output_buffer = BytesIO()
    replaced: set[str] = set()

    try:
        with ZipFile(input_buffer, "r") as source_zip, ZipFile(output_buffer, "w", ZIP_DEFLATED) as target_zip:
            for info in source_zip.infolist():
                content = source_zip.read(info.filename)
                if info.filename == "word/document.xml":
                    xml = content.decode("utf-8")
                    for field, anchors in FIELD_ANCHORS.items():
                        value = _clean(payload.get(field))
                        if not value:
                            continue
                        for anchor in anchors:
                            xml, changed = _replace_anchor_text(xml, anchor, value)
                            if changed:
                                replaced.add(field)
                                break
                    content = xml.encode("utf-8")
                target_zip.writestr(deepcopy(info), content)
    except Exception as exc:  # invalid packages must never be emitted
        raise OfficialProposalDocumentError("Arquivo oficial DOCX inválido ou corrompido.") from exc

    missing_anchors = sorted(REQUIRED_DOCUMENT_FIELDS - replaced)
    if missing_anchors:
        raise OfficialProposalDocumentError(
            "O modelo oficial não contém âncoras contínuas seguras para os campos: " + ", ".join(missing_anchors)
        )

    generated = output_buffer.getvalue()
    filename = f"{output_number}-{template.code}-v{template.version}.docx"
    return GeneratedOfficialDocument(
        filename=filename,
        content=generated,
        sha256=sha256(generated).hexdigest(),
        template_code=template.code,
        template_version=template.version,
        source_sha256=source_hash,
    )


def verify_media_preserved(source: bytes, generated: bytes) -> bool:
    """Guarantee that all embedded images and relationships remain byte-identical."""
    with ZipFile(BytesIO(source), "r") as source_zip, ZipFile(BytesIO(generated), "r") as generated_zip:
        protected = [
            name
            for name in source_zip.namelist()
            if name.startswith("word/media/")
            or name.startswith("word/header")
            or name.startswith("word/footer")
            or name == "word/_rels/document.xml.rels"
        ]
        return all(
            name in generated_zip.namelist() and source_zip.read(name) == generated_zip.read(name)
            for name in protected
        )
