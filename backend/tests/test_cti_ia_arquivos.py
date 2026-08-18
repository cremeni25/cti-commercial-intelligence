from services.ia_comercial_arquivos import gerar_docx_resposta, gerar_pptx_resposta, gerar_xlsx_resposta

META = {"fontes": [{"tipo": "CTI", "descricao": "Teste"}], "artefatos": [{"tipo": "PLANILHA_XLSX", "dados": [{"label": "Supra", "valor": 10, "unidade": "un."}]}]}

def test_xlsx_valido():
    data = gerar_xlsx_resposta("Análise frigorífica", META)
    assert data[:2] == b"PK"

def test_pptx_valido():
    data = gerar_pptx_resposta("Análise frigorífica", META)
    assert data[:2] == b"PK"

def test_docx_valido():
    data = gerar_docx_resposta("Análise frigorífica", META)
    assert data[:2] == b"PK"
