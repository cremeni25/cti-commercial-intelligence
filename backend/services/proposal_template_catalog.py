from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProposalTemplateDefinition:
    code: str
    equipment: str
    source_filename: str
    version: int = 1
    preserves_original_layout: bool = True
    preserves_images: bool = True
    preserves_carrier_branding: bool = True


TEMPLATES: tuple[ProposalTemplateDefinition, ...] = (
    ProposalTemplateDefinition("CITIMAX_280", "CITIMAX 280", "CITIMAX 280.docx"),
    ProposalTemplateDefinition("CITIMAX_400", "CITIMAX 400", "CITIMAX 400.docx"),
    ProposalTemplateDefinition("CITIMAX_500", "CITIMAX 500", "CITIMAX 500.docx"),
    ProposalTemplateDefinition("CITIMAX_D6", "CITIMAX D6", "CITIMAX D6.docx"),
    ProposalTemplateDefinition("CITIMAX_D7", "CITIMAX D7", "CITIMAX D7.docx"),
    ProposalTemplateDefinition("S8", "S8", "S8.docx"),
    ProposalTemplateDefinition("S9", "S9", "S9.docx"),
    ProposalTemplateDefinition("SUPRA_750", "SUPRA 750", "SUPRA 750.docx"),
    ProposalTemplateDefinition("SUPRA_850", "SUPRA 850", "SUPRA 850.docx"),
    ProposalTemplateDefinition("SUPRA_1150", "SUPRA 1150", "SUPRA 1150.docx"),
    ProposalTemplateDefinition("XARIOS_350", "XARIOS 350", "XARIOS 350.docx"),
    ProposalTemplateDefinition("XARIOS_6", "XARIOS 6", "XARIOS 6.docx"),
    ProposalTemplateDefinition("VECTOR_8500", "VECTOR 8500", "Vector 8500.docx"),
    ProposalTemplateDefinition("VECTOR_HE19", "VECTOR HE19", "Vector HE19.docx"),
    ProposalTemplateDefinition("X4_7500", "X4 7500", "X4 7500.docx"),
    ProposalTemplateDefinition("X4_7700", "X4 7700", "X4 7700.docx"),
)


_BY_EQUIPMENT = {item.equipment: item for item in TEMPLATES}


def normalize_equipment(value: str) -> str:
    normalized = " ".join(value.strip().upper().replace("-", " ").split())
    aliases = {
        "S 8": "S8",
        "S 9": "S9",
        "VECTOR HE 19": "VECTOR HE19",
        "X4 7500": "X4 7500",
        "X4 7700": "X4 7700",
    }
    return aliases.get(normalized, normalized)


def template_for_equipment(equipment: str) -> ProposalTemplateDefinition:
    normalized = normalize_equipment(equipment)
    template = _BY_EQUIPMENT.get(normalized)
    if not template:
        supported = ", ".join(item.equipment for item in TEMPLATES)
        raise ValueError(f"Equipamento sem modelo oficial de proposta: {equipment}. Modelos suportados: {supported}")
    return template
