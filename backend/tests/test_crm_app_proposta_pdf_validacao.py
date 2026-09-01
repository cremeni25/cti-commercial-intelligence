from services.docx_pdf_conversion_service import ConvertedPdf
from routers import crm_app_proposta_pdf_validacao_router as modulo


def preparar_pdf(monkeypatch):
    registros = {
        "cti_propostas": {
            "id": "prop-1",
            "numero": "PROP-TESTE",
            "item_oportunidade_id": "item-1",
            "oportunidade_id": "opp-1",
            "cliente_id": "cli-1",
            "status_documento": "EMITIDA",
        },
        "cti_oportunidade_itens": {"id": "item-1"},
        "cti_oportunidades": {"id": "opp-1"},
    }
    monkeypatch.setattr(modulo, "_primeiro", lambda tabela, registro_id, detalhe: registros[tabela])
    monkeypatch.setattr(modulo, "_cliente", lambda cliente_id: {"id": cliente_id, "nome": "Cliente Teste"})
    monkeypatch.setattr(modulo, "validar_documento_para_emissao", lambda proposta, item: None)
    monkeypatch.setattr(
        modulo,
        "build_preview_official_proposal",
        lambda supabase, proposta, item, oportunidade, cliente: {
            "filename": "CITIMAX 400.docx",
            "content": b"docx-oficial",
        },
    )
    monkeypatch.setattr(
        modulo,
        "convert_docx_to_pdf",
        lambda content, filename: ConvertedPdf(
            filename="CITIMAX 400.pdf",
            content=b"%PDF-validado",
            sha256="abc123",
            page_count=4,
        ),
    )


def test_validar_pdf_oficial_e_somente_leitura(monkeypatch):
    preparar_pdf(monkeypatch)
    resultado = modulo.validar_pdf_oficial("prop-1")

    assert resultado["success"] is True
    assert resultado["somente_leitura"] is True
    assert resultado["email_enviado"] is False
    assert resultado["persistido"] is False
    assert resultado["arquivo_pdf"] == "CITIMAX 400.pdf"
    assert resultado["paginas"] == 4
    assert resultado["bytes"] == len(b"%PDF-validado")


def test_visualizar_pdf_oficial_entrega_inline_sem_persistir(monkeypatch):
    preparar_pdf(monkeypatch)
    resposta = modulo.visualizar_pdf_oficial("prop-1")

    assert resposta.status_code == 200
    assert resposta.media_type == "application/pdf"
    assert resposta.body == b"%PDF-validado"
    assert resposta.headers["content-disposition"] == 'inline; filename="PROP-TESTE.pdf"'
    assert resposta.headers["cache-control"] == "private, no-store"
