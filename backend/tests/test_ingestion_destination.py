from core.ingestion_destination import decidir_destino


def test_conteudo_comercial_vai_para_candidato_operacional_sem_promocao_automatica():
    decisao = decidir_destino("COMERCIAL", 0.91, entrada="BACKOFFICE_FONTES")
    assert decisao["destino"] == "CANDIDATO_OPERACIONAL_VALIDACAO"
    assert decisao["promocao_operacional_automatica"] is False
    assert decisao["exige_validacao"] is True
    assert decisao["consumivel_dashboard"] is False


def test_conteudo_tecnico_vai_para_conhecimento_semantico():
    decisao = decidir_destino("TECNICO_PRODUTO", 0.90, entrada="BACKOFFICE_FONTES")
    assert decisao["destino"] == "CONHECIMENTO_SEMANTICO"
    assert decisao["consumivel_ia"] is True
    assert decisao["consumivel_dashboard"] is False


def test_sem_registros_semanticos_fica_em_staging():
    decisao = decidir_destino("COMERCIAL", 0.95, entrada="BACKOFFICE_FONTES", possui_registros_semanticos=False)
    assert decisao["destino"] == "STAGING_GOVERNADO"
    assert decisao["consumivel_ia"] is False
    assert decisao["consumivel_dashboard"] is False


def test_upload_operacional_validado_consumivel_por_dashboard_e_ia():
    decisao = decidir_destino("MERCADO_ANFIR", 0.98, entrada="UPLOAD_OPERACIONAL")
    assert decisao["destino"] == "DOMINIO_OPERACIONAL_VALIDADO"
    assert decisao["promocao_operacional_automatica"] is True
    assert decisao["consumivel_ia"] is True
    assert decisao["consumivel_dashboard"] is True
