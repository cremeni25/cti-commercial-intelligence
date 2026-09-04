from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
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


def _date_br(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    raw = str(value).strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return raw


def _money_br(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return str(value or "")
    formatted = f"{number:,.2f}"
    return "R$ " + formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _snapshot_final(proposal: dict[str, Any]) -> dict[str, Any]:
    snapshot = proposal.get("snapshot_dados")
    if not isinstance(snapshot, dict):
        return {}
    final = snapshot.get("documento_final")
    return dict(final) if isinstance(final, dict) else {}


def _prefer(final: dict[str, Any], final_key: str, source: dict[str, Any] | None, *source_keys: str, default: Any = None) -> Any:
    if final_key in final:
        value = final.get(final_key)
        if value is not None and str(value).strip() != "":
            return value
        if value is False:
            return value
    return _first(source, *source_keys, default=default)


def _sim_nao(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return "SIM" if value else "NÃO"
    text = str(value).strip().upper()
    if text in {"TRUE", "1", "SIM", "S"}:
        return "SIM"
    if text in {"FALSE", "0", "NAO", "NÃO", "N"}:
        return "NÃO"
    return value


def build_proposal_document_payload(
    *,
    proposal: dict[str, Any],
    item: dict[str, Any],
    opportunity: dict[str, Any],
    client: dict[str, Any],
    validate_required: bool = True,
) -> ProposalDocumentPayload:
    template = template_for_equipment(str(_first(item, "equipamento", "modelo_equipamento", "produto", default="")))
    final = _snapshot_final(proposal)

    quantity = int(_first(item, "quantidade", default=1) or 1)
    unit_price = float(_first(item, "preco_unitario", default=0) or 0)
    discount = float(_first(item, "desconto_percentual", default=0) or 0)
    total = round(quantity * unit_price * (1 - discount / 100), 2)

    client_name = _first(client, "razao_social", "nome_fantasia", "nome", "empresa") or _first(opportunity, "cliente_nome", "empresa_nome")
    client_tax_id = _first(client, "cpf_cnpj", "cnpj", "cpf", "documento", "documento_fiscal") or _first(opportunity, "cpf_cnpj", "cnpj", "cpf")
    client_state_registration = _first(client, "inscricao_estadual", "ie", "inscricao", "inscricao_est") or _first(opportunity, "inscricao_estadual", "ie")
    client_address = _first(client, "endereco_completo", "endereco", "logradouro", "address") or _first(opportunity, "endereco_completo", "endereco")
    client_phone = _first(client, "telefone", "celular", "whatsapp", "telefone_principal", "fone") or _first(opportunity, "telefone", "celular", "whatsapp")
    client_email = _first(client, "email", "email_principal", "email_comercial") or _first(opportunity, "email", "email_principal")

    entrada = _prefer(final, "valor_entrada", proposal, "valor_entrada")
    tipo_equipamento = _prefer(final, "tipo_equipamento", item, "configuracao", "tipo_equipamento")
    if template.equipment == "CITIMAX 500AE":
        tipo_equipamento = template.equipment

    fields: dict[str, Any] = {
        "proposal_number": _first(proposal, "numero"),
        "proposal_revision": _first(proposal, "versao", default=1),
        "proposal_date": _date_br(_first(proposal, "emitida_em", "created_at")),
        "billing_company": _first(proposal, "empresa_faturamento", default="Carrier Refrigeração Brasil Ltda"),
        "billing_branch": _first(proposal, "filial_faturamento", "cnpj_faturamento"),
        "client_name": client_name,
        "client_tax_id": client_tax_id,
        "client_state_registration": client_state_registration,
        "client_address": client_address,
        "client_phone": client_phone,
        "client_email": client_email,
        "equipment": template.equipment,
        "configuration": tipo_equipamento,
        "voltage": _prefer(final, "voltagem", proposal, "voltagem"),
        "quantity_intro": quantity,
        "quantity": quantity,
        "unit_price": _money_br(unit_price),
        "discount_percent": discount,
        "total_price": _money_br(total),
        "taxes": _prefer(final, "impostos", item, "impostos", default="04% ICMS/PIS/COFINS"),
        "accessories": _prefer(final, "acessorios", item, "acessorios", "opcionais", default=[]),
        "payment_terms": _prefer(final, "condicao_pagamento", item, "condicao_pagamento"),
        "has_down_payment": _sim_nao(_prefer(final, "possui_entrada", item, "possui_entrada", "entrada_sim_nao")),
        "down_payment_value": _money_br(entrada) if entrada is not None and str(entrada).strip() != "" else None,
        "delivery_type": _prefer(final, "local_entrega", item, "tipo_entrega", "local_entrega"),
        "authorized_service_name_address": _prefer(final, "autorizada_nome_endereco", proposal, "autorizada_nome_endereco"),
        "freight": _prefer(final, "frete", item, "frete"),
        "delivery_deadline": _prefer(final, "prazo_entrega", item, "prazo_entrega"),
        "validity": _date_br(_prefer(final, "validade", item, "validade_condicao") or _first(proposal, "validade")),
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
        "lynx_months": _prefer(final, "lynx_meses", proposal, "lynx_meses"),
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
