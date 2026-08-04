from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.proposal_template_catalog import template_for_equipment


class ProposalDocumentDataError(ValueError):
    pass


@dataclass(frozen=True)
class ProposalDocumentPayload:
    template_code: str
    template_filename: str
    template_version: int
    fields: dict[str, Any]


def _first(source: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = (source or {}).get(key)
        if value is not None and str(value).strip() != "":
            return value
    return default


def _required(fields: dict[str, Any], *names: str) -> None:
    missing = [name for name in names if fields.get(name) is None or str(fields.get(name)).strip() == ""]
    if missing:
        raise ProposalDocumentDataError(
            "Campos obrigatórios ausentes para geração da proposta oficial: " + ", ".join(missing)
        )


def build_proposal_document_payload(
    *,
    proposal: dict[str, Any],
    item: dict[str, Any],
    opportunity: dict[str, Any],
    client: dict[str, Any],
    validate_required: bool = True,
) -> ProposalDocumentPayload:
    template = template_for_equipment(str(_first(item, "equipamento", "modelo_equipamento", "produto", default="")))

    quantity = int(_first(item, "quantidade", default=1) or 1)
    unit_price = float(_first(item, "preco_unitario", default=0) or 0)
    discount = float(_first(item, "desconto_percentual", default=0) or 0)
    total = round(quantity * unit_price * (1 - discount / 100), 2)

    fields: dict[str, Any] = {
        "proposal_number": _first(proposal, "numero"),
        "proposal_revision": _first(proposal, "versao", default=1),
        "proposal_date": _first(proposal, "emitida_em", "created_at"),
        "billing_company": _first(proposal, "empresa_faturamento", default="Carrier Refrigeração Brasil Ltda"),
        "billing_branch": _first(proposal, "filial_faturamento", "cnpj_faturamento"),
        "client_name": _first(client, "razao_social", "nome_fantasia", "nome") or _first(opportunity, "cliente_nome", "empresa_nome"),
        "client_tax_id": _first(client, "cpf_cnpj", "cnpj", "cpf"),
        "client_state_registration": _first(client, "inscricao_estadual", "ie"),
        "client_address": _first(client, "endereco_completo", "endereco"),
        "client_phone": _first(client, "telefone", "celular", "whatsapp"),
        "client_email": _first(client, "email", "email_principal"),
        "equipment": template.equipment,
        "configuration": _first(item, "configuracao", "tipo_equipamento"),
        "voltage": _first(proposal, "voltagem"),
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_percent": discount,
        "total_price": total,
        "taxes": _first(item, "impostos", default="04% ICMS/PIS/COFINS"),
        "accessories": _first(item, "opcionais", "acessorios", default=[]),
        "payment_terms": _first(item, "condicao_pagamento"),
        "has_down_payment": _first(proposal, "possui_entrada") or _first(item, "possui_entrada", "entrada_sim_nao"),
        "down_payment_value": _first(proposal, "valor_entrada"),
        "delivery_type": _first(item, "tipo_entrega", "local_entrega"),
        "authorized_service_name_address": _first(proposal, "autorizada_nome_endereco"),
        "freight": _first(item, "frete"),
        "delivery_deadline": _first(item, "prazo_entrega"),
        "validity": _first(item, "validade_condicao") or _first(proposal, "validade"),
        "commercial_notes": _first(item, "observacoes_comerciais") or _first(proposal, "observacoes"),
        "technical_notes": _first(item, "observacoes_tecnicas"),
        "body_width_m": _first(opportunity, "bau_largura_m", "largura_bau_m"),
        "body_length_m": _first(opportunity, "bau_comprimento_m", "comprimento_bau_m"),
        "body_height_m": _first(opportunity, "bau_altura_m", "altura_bau_m"),
        "body_partition_m": _first(opportunity, "bau_divisoria_m", "divisoria_bau_m"),
        "body_doors": _first(opportunity, "bau_portas_qtd", "portas_bau_qtd"),
        "insulation_type": _first(opportunity, "isolamento_tipo"),
        "insulation_front_cm": _first(opportunity, "isolamento_frente_cm"),
        "insulation_roof_cm": _first(opportunity, "isolamento_teto_cm"),
        "insulation_side_cm": _first(opportunity, "isolamento_lateral_cm"),
        "insulation_floor_cm": _first(opportunity, "isolamento_piso_cm"),
        "insulation_door_cm": _first(opportunity, "isolamento_porta_cm"),
        "transport_temperature_c": _first(opportunity, "temperatura_transporte_c", "temperatura_transporte"),
        "door_openings": _first(opportunity, "aberturas_porta_qtd", "numero_aberturas_porta"),
        "door_open_duration_min": _first(opportunity, "duracao_abertura_min"),
        "delivery_period_h": _first(opportunity, "periodo_entrega_h", "periodo_entrega_horas"),
        "lynx_included": _first(item, "lynx_incluido", "lynx_fleet"),
        "lynx_months": _first(proposal, "lynx_meses"),
        "responsible_id": _first(opportunity, "responsavel_id") or _first(proposal, "responsavel_id"),
    }

    if validate_required:
        _required(
            fields,
            "proposal_number",
            "client_name",
            "client_tax_id",
            "client_address",
            "client_email",
            "equipment",
            "quantity",
            "unit_price",
            "total_price",
            "payment_terms",
            "validity",
        )

    return ProposalDocumentPayload(
        template_code=template.code,
        template_filename=template.source_filename,
        template_version=template.version,
        fields=fields,
    )
