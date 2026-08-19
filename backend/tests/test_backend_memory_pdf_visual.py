import inspect

from services import ia_comercial_anexos, ia_comercial_pdf_visual


def test_anexos_nao_carregam_parsers_pesados_no_import_global():
    fonte = inspect.getsource(ia_comercial_anexos)
    cabecalho = fonte.split("MAX_ARQUIVO_BYTES", 1)[0]
    assert "from openpyxl import" not in cabecalho
    assert "from pypdf import" not in cabecalho
    assert "from docx import" not in cabecalho
    assert "from pptx import" not in cabecalho
    assert "from services.ia_comercial_pdf_visual import" not in cabecalho


def test_pdf_visual_nao_duplica_arquivo_com_b64encode_e_usa_file_id():
    fonte = inspect.getsource(ia_comercial_pdf_visual.extrair_pdf_visual)
    assert "b64encode" not in fonte
    assert "files.create" in fonte
    assert 'purpose="user_data"' in fonte
    assert '"file_id": arquivo.id' in fonte
    assert "files.delete" in fonte


def test_pdf_visual_define_expiracao_defensiva():
    fonte = inspect.getsource(ia_comercial_pdf_visual.extrair_pdf_visual)
    assert '"seconds": 3600' in fonte
