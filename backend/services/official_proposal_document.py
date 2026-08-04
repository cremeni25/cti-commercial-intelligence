from __future__ import annotations

import html
import re
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from typing import Any, Mapping
from zipfile import ZIP_DEFLATED, ZipFile

from services.proposal_template_catalog import template_for_equipment


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
    "lynx_periodo_meses": ("Período:",),
    "validade": ("Validade da proposta:",),
}

PAYLOAD_FIELD_MAP: dict[str, str] = {
    "proposal_date": "data",
    "client_name": "cliente_nome",
    "client_tax_id": "cpf_cnpj",
    "client_state_registration": "inscricao_estadual",
    "client_address": "endereco_completo",
    "client_phone": "telefones",
    "client_email": "email",
    "voltage": "voltagem",
    "quantity": "quantidade",
    "unit_price": "valor_unitario",
    "total_price": "valor_total",
    "accessories": "acessorios",
    "payment_terms": "condicoes_pagamento",
    "down_payment_value": "valor_entrada",
    "authorized_service_name_address": "autorizada",
    "lynx_months": "lynx_periodo_meses",
    "validity": "validade",
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

_TEXT_NODE = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.DOTALL)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        value = ", ".join(str(item) for item in value if item is not None)
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def _document_fields(payload: Any) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        source = dict(payload)
    else:
        source = dict(getattr(payload, "fields", {}) or {})
    if not source:
        raise OfficialProposalDocumentError("Payload documental inválido ou vazio.")
    if any(key in FIELD_ANCHORS for key in source):
        return source
    return {document_key: source.get(internal_key) for internal_key, document_key in PAYLOAD_FIELD_MAP.items()}


def validate_document_payload(payload: Mapping[str, Any]) -> None:
    missing = sorted(key for key in REQUIRED_DOCUMENT_FIELDS if not _clean(payload.get(key)))
    if missing:
        raise OfficialProposalDocumentError(
            "Dados obrigatórios ausentes para emissão do documento oficial: " + ", ".join(missing)
        )


def _replace_anchor_text(xml: str, anchor: str, value: str) -> tuple[str, bool]:
    """Insere o valor após uma âncora mesmo quando o Word a dividiu em vários runs."""
    nodes = list(_TEXT_NODE.finditer(xml))
    if not nodes:
        return xml, False

    visible_parts: list[str] = []
    ranges: list[tuple[int, int, re.Match[str]]] = []
    cursor = 0
    for node in nodes:
        text = html.unescape(node.group(1))
        start = cursor
        cursor += len(text)
        visible_parts.append(text)
        ranges.append((start, cursor, node))

    visible = "".join(visible_parts)
    position = visible.find(anchor)
    if position < 0:
        return xml, False
    anchor_end = position + len(anchor)

    target = next((node for start, end, node in ranges if start < anchor_end <= end), None)
    if target is None:
        return xml, False

    escaped_value = html.escape(value, quote=False)
    insertion = target.end(1)
    return xml[:insertion] + " " + escaped_value + xml[insertion:], True


def render_official_docx(
    source: bytes,
    equipment: str,
    payload: Any,
    *,
    output_number: str,
    validate_required: bool = True,
    require_all_requested_anchors: bool = True,
) -> GeneratedOfficialDocument:
    template = template_for_equipment(equipment)
    if not template.source_filename.lower().endswith(".docx"):
        raise OfficialProposalDocumentError(
            f"O modelo {template.equipment} está em formato DOC legado e precisa ser convertido para DOCX "
            "sem alteração visual antes da emissão automatizada."
        )

    document_fields = _document_fields(payload)
    if validate_required:
        validate_document_payload(document_fields)

    source_hash = sha256(source).hexdigest()
    input_buffer = BytesIO(source)
    output_buffer = BytesIO()
    replaced: set[str] = set()
    requested = {key for key, value in document_fields.items() if _clean(value)}

    try:
        with ZipFile(input_buffer, "r") as source_zip, ZipFile(output_buffer, "w", ZIP_DEFLATED) as target_zip:
            for info in source_zip.infolist():
                content = source_zip.read(info.filename)
                if info.filename == "word/document.xml":
                    xml = content.decode("utf-8")
                    for field, anchors in FIELD_ANCHORS.items():
                        value = _clean(document_fields.get(field))
                        if not value:
                            continue
                        for anchor in anchors:
                            xml, changed = _replace_anchor_text(xml, anchor, value)
                            if changed:
                                replaced.add(field)
                                break
                    content = xml.encode("utf-8")
                target_zip.writestr(deepcopy(info), content)
    except Exception as exc:
        raise OfficialProposalDocumentError("Arquivo oficial DOCX inválido ou corrompido.") from exc

    required_anchors = REQUIRED_DOCUMENT_FIELDS if validate_required else requested
    missing_anchors = sorted(required_anchors - replaced)
    if missing_anchors and require_all_requested_anchors:
        raise OfficialProposalDocumentError(
            "O modelo oficial não contém âncoras seguras para os campos: " + ", ".join(missing_anchors)
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
