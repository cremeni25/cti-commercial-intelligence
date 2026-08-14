from routers import backoffice_fontes_router as fontes


def test_detecta_formatos_universais_principais():
    casos = {
        "relatorio.pdf": "PDF",
        "proposta.docx": "WORD",
        "apresentacao.pptx": "POWERPOINT",
        "dados.xlsx": "PLANILHA",
        "imagem.png": "IMAGEM",
        "notas.txt": "TEXTO",
        "payload.json": "DADOS_ESTRUTURADOS",
    }
    for nome, esperado in casos.items():
        tipo, _ = fontes._tipo_detectado(nome, None)
        assert tipo == esperado


def test_upload_nao_publica_automaticamente_para_ia():
    assert "PUBLICADO_IA" not in fontes.TRANSICOES_ADMIN["RECEBIDO"]
    assert "HOMOLOGADO" not in fontes.TRANSICOES_ADMIN["RECEBIDO"]
    assert fontes.TRANSICOES_ADMIN["INTERPRETADO"] == {"VALIDADO", "REJEITADO"}
    assert fontes.TRANSICOES_ADMIN["VALIDADO"] == {"HOMOLOGADO", "REJEITADO"}
    assert "PUBLICADO_IA" not in fontes.TRANSICOES_ADMIN["HOMOLOGADO"]


def test_nome_seguro_remove_caminho_e_caracteres_perigosos():
    nome = fontes._nome_seguro("../../Relatório Comercial 2026?.pdf")
    assert "/" not in nome
    assert ".." not in nome
    assert nome.endswith(".pdf")
