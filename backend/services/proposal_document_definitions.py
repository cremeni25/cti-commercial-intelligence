from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProposalDocumentField:
    """Campo variável pertencente exclusivamente a um documento oficial."""

    code: str
    label: str
    occurrence: str


@dataclass(frozen=True)
class ProposalDocumentDefinition:
    code: str
    equipment: str
    source_filename: str
    page: int
    fields: tuple[ProposalDocumentField, ...]


def _field(document_code: str, name: str, label: str, occurrence: str = "campo") -> ProposalDocumentField:
    return ProposalDocumentField(
        code=f"{document_code.lower()}.{name}",
        label=label,
        occurrence=occurrence,
    )


CITIMAX_280 = ProposalDocumentDefinition(
    code="CITIMAX_280",
    equipment="CITIMAX 280",
    source_filename="CITIMAX 280.docx",
    page=1,
    fields=(
        _field("CITIMAX_280", "data", "Data"),
        _field("CITIMAX_280", "cliente_nome", "Nome do cliente"),
        _field("CITIMAX_280", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("CITIMAX_280", "cliente_inscricao_estadual", "INSC"),
        _field("CITIMAX_280", "cliente_endereco_completo", "Endereço Completo"),
        _field("CITIMAX_280", "cliente_telefones", "Telefones de contato"),
        _field("CITIMAX_280", "cliente_email", "E-mail"),
        _field("CITIMAX_280", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("CITIMAX_280", "voltagem", "Voltagem"),
        _field("CITIMAX_280", "quantidade", "Quantidade"),
        _field("CITIMAX_280", "valor_unitario", "Valor unitário desta proposta"),
        _field("CITIMAX_280", "valor_total", "Valor Total desta proposta"),
        _field("CITIMAX_280", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("CITIMAX_280", "condicoes_pagamento", "Condições de pagamentos"),
        _field("CITIMAX_280", "valor_entrada", "Valor da entrada"),
        _field("CITIMAX_280", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


CITIMAX_400 = ProposalDocumentDefinition(
    code="CITIMAX_400",
    equipment="CITIMAX 400",
    source_filename="CITIMAX 400.docx",
    page=1,
    fields=(
        _field("CITIMAX_400", "data", "Data"),
        _field("CITIMAX_400", "cliente_nome", "Nome do cliente"),
        _field("CITIMAX_400", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("CITIMAX_400", "cliente_inscricao_estadual", "INSC"),
        _field("CITIMAX_400", "cliente_endereco_completo", "Endereço Completo"),
        _field("CITIMAX_400", "cliente_telefones", "Telefones de contato"),
        _field("CITIMAX_400", "cliente_email", "E-mail"),
        _field("CITIMAX_400", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("CITIMAX_400", "voltagem", "Voltagem"),
        _field("CITIMAX_400", "quantidade", "Quantidade"),
        _field("CITIMAX_400", "valor_unitario", "Valor unitário desta proposta"),
        _field("CITIMAX_400", "valor_total", "Valor Total desta proposta"),
        _field("CITIMAX_400", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("CITIMAX_400", "condicoes_pagamento", "Condições de pagamentos"),
        _field("CITIMAX_400", "valor_entrada", "Valor da entrada"),
        _field("CITIMAX_400", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


CITIMAX_500 = ProposalDocumentDefinition(
    code="CITIMAX_500",
    equipment="CITIMAX 500",
    source_filename="CITIMAX 500.doc",
    page=1,
    fields=(
        _field("CITIMAX_500", "data", "Data"),
        _field("CITIMAX_500", "cliente_nome", "Nome do cliente"),
        _field("CITIMAX_500", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("CITIMAX_500", "cliente_inscricao_estadual", "INSC"),
        _field("CITIMAX_500", "cliente_endereco_completo", "Endereço Completo"),
        _field("CITIMAX_500", "cliente_telefones", "Telefones de contato"),
        _field("CITIMAX_500", "cliente_email", "E-mail"),
        _field("CITIMAX_500", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("CITIMAX_500", "voltagem", "Voltagem"),
        _field("CITIMAX_500", "quantidade", "Quantidade"),
        _field("CITIMAX_500", "valor_unitario", "Valor unitário desta proposta"),
        _field("CITIMAX_500", "valor_total", "Valor Total desta proposta"),
        _field("CITIMAX_500", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("CITIMAX_500", "condicoes_pagamento", "Condições de pagamentos"),
        _field("CITIMAX_500", "valor_entrada", "Valor da entrada"),
        _field("CITIMAX_500", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


CITIMAX_D6 = ProposalDocumentDefinition(
    code="CITIMAX_D6",
    equipment="CITIMAX D6",
    source_filename="CITIMAX D6.docx",
    page=1,
    fields=(
        _field("CITIMAX_D6", "data", "Data"),
        _field("CITIMAX_D6", "cliente_nome", "Nome do cliente"),
        _field("CITIMAX_D6", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("CITIMAX_D6", "cliente_inscricao_estadual", "INSC"),
        _field("CITIMAX_D6", "cliente_endereco_completo", "Endereço Completo"),
        _field("CITIMAX_D6", "cliente_telefones", "Telefones de contato"),
        _field("CITIMAX_D6", "cliente_email", "E-mail"),
        _field("CITIMAX_D6", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("CITIMAX_D6", "voltagem", "Voltagem"),
        _field("CITIMAX_D6", "quantidade", "Quantidade"),
        _field("CITIMAX_D6", "valor_unitario", "Valor unitário desta proposta"),
        _field("CITIMAX_D6", "valor_total", "Valor Total desta proposta"),
        _field("CITIMAX_D6", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("CITIMAX_D6", "condicoes_pagamento", "Condições de pagamentos"),
        _field("CITIMAX_D6", "valor_entrada", "Valor da entrada"),
        _field("CITIMAX_D6", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


CITIMAX_D7 = ProposalDocumentDefinition(
    code="CITIMAX_D7",
    equipment="CITIMAX D7",
    source_filename="CITIMAX D7.docx",
    page=1,
    fields=(
        _field("CITIMAX_D7", "data", "Data"),
        _field("CITIMAX_D7", "cliente_nome", "Nome do cliente"),
        _field("CITIMAX_D7", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("CITIMAX_D7", "cliente_inscricao_estadual", "INSC"),
        _field("CITIMAX_D7", "cliente_endereco_completo", "Endereço Completo"),
        _field("CITIMAX_D7", "cliente_telefones", "Telefones de contato"),
        _field("CITIMAX_D7", "cliente_email", "E-mail"),
        _field("CITIMAX_D7", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("CITIMAX_D7", "voltagem", "Voltagem"),
        _field("CITIMAX_D7", "quantidade", "Quantidade"),
        _field("CITIMAX_D7", "valor_unitario", "Valor unitário desta proposta"),
        _field("CITIMAX_D7", "valor_total", "Valor Total desta proposta"),
        _field("CITIMAX_D7", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("CITIMAX_D7", "condicoes_pagamento", "Condições de pagamentos"),
        _field("CITIMAX_D7", "valor_entrada", "Valor da entrada"),
        _field("CITIMAX_D7", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


S8 = ProposalDocumentDefinition(
    code="S8",
    equipment="S8",
    source_filename="S8.docx",
    page=1,
    fields=(
        _field("S8", "data", "Data"),
        _field("S8", "cliente_nome", "Nome do cliente"),
        _field("S8", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("S8", "cliente_inscricao_estadual", "INSC"),
        _field("S8", "cliente_endereco_completo", "Endereço Completo"),
        _field("S8", "cliente_telefones", "Telefones de contato"),
        _field("S8", "cliente_email", "E-mail"),
        _field("S8", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("S8", "quantidade", "Quantidade"),
        _field("S8", "valor_unitario", "Valor unitário desta proposta"),
        _field("S8", "valor_total", "Valor Total desta proposta"),
        _field("S8", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("S8", "condicoes_pagamento", "Condições de pagamentos"),
        _field("S8", "valor_entrada", "Valor da entrada"),
        _field("S8", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


S9 = ProposalDocumentDefinition(
    code="S9",
    equipment="S9",
    source_filename="S9.docx",
    page=1,
    fields=(
        _field("S9", "data", "Data"),
        _field("S9", "cliente_nome", "Nome do cliente"),
        _field("S9", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("S9", "cliente_inscricao_estadual", "INSC"),
        _field("S9", "cliente_endereco_completo", "Endereço Completo"),
        _field("S9", "cliente_telefones", "Telefones de contato"),
        _field("S9", "cliente_email", "E-mail"),
        _field("S9", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("S9", "quantidade", "Quantidade"),
        _field("S9", "valor_unitario", "Valor unitário desta proposta"),
        _field("S9", "valor_total", "Valor Total desta proposta"),
        _field("S9", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("S9", "condicoes_pagamento", "Condições de pagamentos"),
        _field("S9", "valor_entrada", "Valor da entrada"),
        _field("S9", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


SUPRA_750 = ProposalDocumentDefinition(
    code="SUPRA_750",
    equipment="SUPRA 750",
    source_filename="SUPRA 750.docx",
    page=1,
    fields=(
        _field("SUPRA_750", "data", "Data"),
        _field("SUPRA_750", "cliente_nome", "Nome do cliente"),
        _field("SUPRA_750", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("SUPRA_750", "cliente_inscricao_estadual", "INSC"),
        _field("SUPRA_750", "cliente_endereco_completo", "Endereço Completo"),
        _field("SUPRA_750", "cliente_telefones", "Telefones de contato"),
        _field("SUPRA_750", "cliente_email", "E-mail"),
        _field("SUPRA_750", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("SUPRA_750", "quantidade", "Quantidade"),
        _field("SUPRA_750", "valor_unitario", "Valor unitário desta proposta"),
        _field("SUPRA_750", "valor_total", "Valor Total desta proposta"),
        _field("SUPRA_750", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("SUPRA_750", "condicoes_pagamento", "Condições de pagamentos"),
        _field("SUPRA_750", "valor_entrada", "Valor da entrada"),
        _field("SUPRA_750", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


SUPRA_850 = ProposalDocumentDefinition(
    code="SUPRA_850",
    equipment="SUPRA 850",
    source_filename="SUPRA 850.docx",
    page=1,
    fields=(
        _field("SUPRA_850", "data", "Data"),
        _field("SUPRA_850", "cliente_nome", "Nome do cliente"),
        _field("SUPRA_850", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("SUPRA_850", "cliente_inscricao_estadual", "INSC"),
        _field("SUPRA_850", "cliente_endereco_completo", "Endereço Completo"),
        _field("SUPRA_850", "cliente_telefones", "Telefones de contato"),
        _field("SUPRA_850", "cliente_email", "E-mail"),
        _field("SUPRA_850", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("SUPRA_850", "quantidade", "Quantidade"),
        _field("SUPRA_850", "valor_unitario", "Valor unitário desta proposta"),
        _field("SUPRA_850", "valor_total", "Valor Total desta proposta"),
        _field("SUPRA_850", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("SUPRA_850", "condicoes_pagamento", "Condições de pagamentos"),
        _field("SUPRA_850", "valor_entrada", "Valor da entrada"),
        _field("SUPRA_850", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


SUPRA_1150 = ProposalDocumentDefinition(
    code="SUPRA_1150",
    equipment="SUPRA 1150",
    source_filename="SUPRA 1150.docx",
    page=1,
    fields=(
        _field("SUPRA_1150", "data", "Data"),
        _field("SUPRA_1150", "cliente_nome", "Nome do cliente"),
        _field("SUPRA_1150", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("SUPRA_1150", "cliente_inscricao_estadual", "INSC"),
        _field("SUPRA_1150", "cliente_endereco_completo", "Endereço Completo"),
        _field("SUPRA_1150", "cliente_telefones", "Telefones de contato"),
        _field("SUPRA_1150", "cliente_email", "E-mail"),
        _field("SUPRA_1150", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("SUPRA_1150", "quantidade", "Quantidade"),
        _field("SUPRA_1150", "valor_unitario", "Valor unitário desta proposta"),
        _field("SUPRA_1150", "valor_total", "Valor Total desta proposta"),
        _field("SUPRA_1150", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("SUPRA_1150", "condicoes_pagamento", "Condições de pagamentos"),
        _field("SUPRA_1150", "valor_entrada", "Valor da entrada"),
        _field("SUPRA_1150", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


VECTOR_8500 = ProposalDocumentDefinition(
    code="VECTOR_8500",
    equipment="VECTOR 8500",
    source_filename="Vector 8500.docx",
    page=1,
    fields=(
        _field("VECTOR_8500", "data", "Data"),
        _field("VECTOR_8500", "cliente_nome", "Nome do cliente"),
        _field("VECTOR_8500", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("VECTOR_8500", "cliente_inscricao_estadual", "INSC"),
        _field("VECTOR_8500", "cliente_endereco_completo", "Endereço Completo"),
        _field("VECTOR_8500", "cliente_telefones", "Telefones de contato"),
        _field("VECTOR_8500", "cliente_email", "E-mail"),
        _field("VECTOR_8500", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("VECTOR_8500", "quantidade", "Quantidade"),
        _field("VECTOR_8500", "valor_unitario", "Valor unitário desta proposta"),
        _field("VECTOR_8500", "valor_total", "Valor Total desta proposta"),
        _field("VECTOR_8500", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("VECTOR_8500", "condicoes_pagamento", "Condições de pagamentos"),
        _field("VECTOR_8500", "valor_entrada", "Valor da entrada"),
        _field("VECTOR_8500", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
        _field("VECTOR_8500", "lynx_periodo_meses", "Período de Lynx Fleet"),
    ),
)


VECTOR_HE19 = ProposalDocumentDefinition(
    code="VECTOR_HE19",
    equipment="VECTOR HE19",
    source_filename="Vector HE19.docx",
    page=1,
    fields=(
        _field("VECTOR_HE19", "data", "Data"),
        _field("VECTOR_HE19", "cliente_nome", "Nome do cliente"),
        _field("VECTOR_HE19", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("VECTOR_HE19", "cliente_inscricao_estadual", "INSC"),
        _field("VECTOR_HE19", "cliente_endereco_completo", "Endereço Completo"),
        _field("VECTOR_HE19", "cliente_telefones", "Telefones de contato"),
        _field("VECTOR_HE19", "cliente_email", "E-mail"),
        _field("VECTOR_HE19", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("VECTOR_HE19", "quantidade", "Quantidade"),
        _field("VECTOR_HE19", "valor_unitario", "Valor unitário desta proposta"),
        _field("VECTOR_HE19", "valor_total", "Valor Total desta proposta"),
        _field("VECTOR_HE19", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("VECTOR_HE19", "condicoes_pagamento", "Condições de pagamentos"),
        _field("VECTOR_HE19", "valor_entrada", "Valor da entrada"),
        _field("VECTOR_HE19", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
        _field("VECTOR_HE19", "lynx_periodo_meses", "Período de Lynx Fleet"),
    ),
)


X4_7500 = ProposalDocumentDefinition(
    code="X4_7500",
    equipment="X4 7500",
    source_filename="X4 7500.docx",
    page=1,
    fields=(
        _field("X4_7500", "data", "Data"),
        _field("X4_7500", "cliente_nome", "Nome do cliente"),
        _field("X4_7500", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("X4_7500", "cliente_inscricao_estadual", "INSC"),
        _field("X4_7500", "cliente_endereco_completo", "Endereço Completo"),
        _field("X4_7500", "cliente_telefones", "Telefones de contato"),
        _field("X4_7500", "cliente_email", "E-mail"),
        _field("X4_7500", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("X4_7500", "quantidade", "Quantidade"),
        _field("X4_7500", "valor_unitario", "Valor unitário desta proposta"),
        _field("X4_7500", "valor_total", "Valor Total desta proposta"),
        _field("X4_7500", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("X4_7500", "condicoes_pagamento", "Condições de pagamentos"),
        _field("X4_7500", "valor_entrada", "Valor da entrada"),
        _field("X4_7500", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
        _field("X4_7500", "lynx_periodo_meses", "Período de Lynx Fleet"),
    ),
)


X4_7700 = ProposalDocumentDefinition(
    code="X4_7700",
    equipment="X4 7700",
    source_filename="X4 7700.docx",
    page=1,
    fields=(
        _field("X4_7700", "data", "Data"),
        _field("X4_7700", "cliente_nome", "Nome do cliente"),
        _field("X4_7700", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("X4_7700", "cliente_inscricao_estadual", "INSC"),
        _field("X4_7700", "cliente_endereco_completo", "Endereço Completo"),
        _field("X4_7700", "cliente_telefones", "Telefones de contato"),
        _field("X4_7700", "cliente_email", "E-mail"),
        _field("X4_7700", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("X4_7700", "quantidade", "Quantidade"),
        _field("X4_7700", "valor_unitario", "Valor unitário desta proposta"),
        _field("X4_7700", "valor_total", "Valor Total desta proposta"),
        _field("X4_7700", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("X4_7700", "condicoes_pagamento", "Condições de pagamentos"),
        _field("X4_7700", "valor_entrada", "Valor da entrada"),
        _field("X4_7700", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
        _field("X4_7700", "lynx_periodo_meses", "Período de Lynx Fleet"),
    ),
)


XARIOS_350 = ProposalDocumentDefinition(
    code="XARIOS_350",
    equipment="XARIOS 350",
    source_filename="XARIOS 350.doc",
    page=1,
    fields=(
        _field("XARIOS_350", "data", "Data"),
        _field("XARIOS_350", "cliente_nome", "Nome do cliente"),
        _field("XARIOS_350", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("XARIOS_350", "cliente_inscricao_estadual", "INSC"),
        _field("XARIOS_350", "cliente_endereco_completo", "Endereço Completo"),
        _field("XARIOS_350", "cliente_telefones", "Telefones de contato"),
        _field("XARIOS_350", "cliente_email", "E-mail"),
        _field("XARIOS_350", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("XARIOS_350", "voltagem", "Voltagem"),
        _field("XARIOS_350", "quantidade", "Quantidade"),
        _field("XARIOS_350", "valor_unitario", "Valor unitário desta proposta"),
        _field("XARIOS_350", "valor_total", "Valor Total desta proposta"),
        _field("XARIOS_350", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("XARIOS_350", "condicoes_pagamento", "Condições de pagamentos"),
        _field("XARIOS_350", "valor_entrada", "Valor da entrada"),
        _field("XARIOS_350", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


XARIOS_6 = ProposalDocumentDefinition(
    code="XARIOS_6",
    equipment="XARIOS 6",
    source_filename="XARIOS 6.doc",
    page=1,
    fields=(
        _field("XARIOS_6", "data", "Data"),
        _field("XARIOS_6", "cliente_nome", "Nome do cliente"),
        _field("XARIOS_6", "cliente_cpf_cnpj", "CPF/CNPJ"),
        _field("XARIOS_6", "cliente_inscricao_estadual", "INSC"),
        _field("XARIOS_6", "cliente_endereco_completo", "Endereço Completo"),
        _field("XARIOS_6", "cliente_telefones", "Telefones de contato"),
        _field("XARIOS_6", "cliente_email", "E-mail"),
        _field("XARIOS_6", "quantidade_texto", "Quantidade no texto introdutório", "texto"),
        _field("XARIOS_6", "voltagem", "Voltagem"),
        _field("XARIOS_6", "quantidade", "Quantidade"),
        _field("XARIOS_6", "valor_unitario", "Valor unitário desta proposta"),
        _field("XARIOS_6", "valor_total", "Valor Total desta proposta"),
        _field("XARIOS_6", "acessorios_itens_complementares", "Acessórios / Itens Complementares"),
        _field("XARIOS_6", "condicoes_pagamento", "Condições de pagamentos"),
        _field("XARIOS_6", "valor_entrada", "Valor da entrada"),
        _field("XARIOS_6", "autorizada_nome_endereco", "Nome e endereço da Autorizada"),
    ),
)


DOCUMENT_DEFINITIONS: tuple[ProposalDocumentDefinition, ...] = (
    CITIMAX_280,
    CITIMAX_400,
    CITIMAX_500,
    CITIMAX_D6,
    CITIMAX_D7,
    S8,
    S9,
    SUPRA_750,
    SUPRA_850,
    SUPRA_1150,
    VECTOR_8500,
    VECTOR_HE19,
    X4_7500,
    X4_7700,
    XARIOS_350,
    XARIOS_6,
)


_BY_EQUIPMENT = {definition.equipment: definition for definition in DOCUMENT_DEFINITIONS}


def document_definition_for_equipment(equipment: str) -> ProposalDocumentDefinition:
    normalized = " ".join(equipment.strip().upper().replace("-", " ").split())
    aliases = {
        "S 8": "S8",
        "S 9": "S9",
        "VECTOR HE 19": "VECTOR HE19",
    }
    normalized = aliases.get(normalized, normalized)
    definition = _BY_EQUIPMENT.get(normalized)
    if definition is None:
        raise ValueError(f"Equipamento sem definição documental independente: {equipment}")
    return definition
