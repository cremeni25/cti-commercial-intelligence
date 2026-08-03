from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from services.official_proposal_document import (
    OfficialProposalDocumentError,
    render_official_docx,
    validate_document_payload,
    verify_media_preserved,
)


PAYLOAD = {
    "data": "03/08/2026",
    "cliente_nome": "Cliente Teste Ltda",
    "cpf_cnpj": "12.345.678/0001-90",
    "inscricao_estadual": "123.456.789.000",
    "endereco_completo": "Rua Teste, 100 - São Paulo/SP",
    "telefones": "(11) 99999-9999",
    "email": "cliente@example.com",
    "voltagem": "220V",
    "quantidade": "2",
    "valor_unitario": "R$ 100.000,00",
    "valor_total": "R$ 200.000,00",
    "acessorios": "Kit instalação",
    "condicoes_pagamento": "30% de entrada e saldo faturado",
    "valor_entrada": "R$ 60.000,00",
    "autorizada": "Rede Carrier São Paulo",
    "validade": "31/08/2026",
}


def fake_docx() -> bytes:
    document = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
    <w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body>
    """ + "".join(f"<w:p><w:r><w:t>{anchor}</w:t></w:r></w:p>" for anchor in [
        "Data:", "Nome do cliente:", "CPF/CNPJ:", "INSC:", "Endereço Completo:",
        "Telefones de contato:", "E-mail:", "Voltagem:", "Quantidade:",
        "Valor unitário desta proposta:", "Valor Total desta proposta:",
        "Acessórios / Itens Complementares:", "Condições de pagamentos:",
        "Valor:", "Nome e endereço da Autorizada:", "Validade da proposta:"
    ]) + "</w:body></w:document>"
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as package:
        package.writestr("word/document.xml", document)
        package.writestr("word/media/equipamento.png", b"imagem-equipamento-original")
        package.writestr("word/header1.xml", b"logo-carrier-no-cabecalho")
        package.writestr("word/footer1.xml", b"rodape-oficial")
        package.writestr("word/_rels/document.xml.rels", b"relacionamentos-originais")
    return buffer.getvalue()


def test_missing_required_document_data_blocks_generation():
    incomplete = dict(PAYLOAD)
    incomplete["cpf_cnpj"] = ""
    with pytest.raises(OfficialProposalDocumentError, match="cpf_cnpj"):
        validate_document_payload(incomplete)


def test_generation_preserves_images_branding_headers_and_relationships():
    source = fake_docx()
    result = render_official_docx(source, "SUPRA 750", PAYLOAD, output_number="PROP-TESTE")
    assert result.filename == "PROP-TESTE-SUPRA_750-v1.docx"
    assert result.sha256
    assert result.source_sha256
    assert verify_media_preserved(source, result.content)
    with ZipFile(BytesIO(result.content), "r") as generated:
        xml = generated.read("word/document.xml").decode("utf-8")
        assert "Nome do cliente: Cliente Teste Ltda" in xml
        assert "Valor Total desta proposta: R$ 200.000,00" in xml


def test_legacy_doc_is_never_recreated_or_approximated():
    with pytest.raises(OfficialProposalDocumentError, match="DOC legado"):
        render_official_docx(b"legacy", "CITIMAX 500", PAYLOAD, output_number="PROP-TESTE")


def test_missing_anchor_blocks_document_instead_of_changing_layout():
    source = fake_docx()
    broken = BytesIO()
    with ZipFile(BytesIO(source), "r") as original, ZipFile(broken, "w", ZIP_DEFLATED) as package:
        for info in original.infolist():
            content = original.read(info.filename)
            if info.filename == "word/document.xml":
                content = content.replace(b"CPF/CNPJ:", b"CAMPO REMOVIDO")
            package.writestr(info, content)
    with pytest.raises(OfficialProposalDocumentError, match="cpf_cnpj"):
        render_official_docx(broken.getvalue(), "SUPRA 750", PAYLOAD, output_number="PROP-TESTE")
