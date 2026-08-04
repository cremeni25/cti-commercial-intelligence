from routers.modelos_proposta_reconciliacao_router import _indice_por_nome, _linha_produto


def test_indexa_arquivos_por_nome_sem_perder_caminho():
    indice = _indice_por_nome([
        "trailer/vector-8500/v1/Vector 8500.docx",
        "trailer/x4-7500/v1/X4 7500.docx",
    ])

    assert indice["vector 8500.docx"] == ["trailer/vector-8500/v1/Vector 8500.docx"]
    assert indice["x4 7500.docx"] == ["trailer/x4-7500/v1/X4 7500.docx"]


def test_classifica_quatro_modelos_ausentes_como_trailer():
    for equipamento in ("VECTOR 8500", "VECTOR HE19", "X4 7500", "X4 7700"):
        assert _linha_produto(equipamento) == "TRAILER"


def test_classifica_demais_linhas_comerciais():
    assert _linha_produto("SUPRA 750") == "DIESEL TRUCK"
    assert _linha_produto("CITIMAX D6") == "DIESEL TRUCK"
    assert _linha_produto("CITIMAX 280") == "DIRECT DRIVE"
    assert _linha_produto("XARIOS 350") == "DIRECT DRIVE"
