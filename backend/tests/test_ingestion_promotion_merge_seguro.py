from core.ingestion_promotion import planejar_merge_sem_sobrescrita


def test_merge_seguro_preenche_apenas_campo_vazio():
    existente = {"nome": "Cliente A", "cnpj": "123", "cidade": None, "email": "a@x.com"}
    novo = {"nome": "Cliente A", "cnpj": "123", "cidade": "Sao Paulo", "email": "a@x.com"}

    plano = planejar_merge_sem_sobrescrita(existente, novo)

    assert plano["seguro"] is True
    assert plano["mesclado"]["cidade"] == "Sao Paulo"
    assert plano["campos_preenchidos"] == ["cidade"]


def test_merge_seguro_bloqueia_troca_de_valor_existente():
    existente = {"nome": "Cliente A", "cnpj": "123", "cidade": "Sao Paulo"}
    novo = {"nome": "Cliente A", "cnpj": "123", "cidade": "Campinas"}

    plano = planejar_merge_sem_sobrescrita(existente, novo)

    assert plano["seguro"] is False
    assert plano["mesclado"]["cidade"] == "Sao Paulo"
    assert plano["conflitos"] == [{
        "campo": "cidade",
        "valor_existente": "Sao Paulo",
        "valor_recebido": "Campinas",
    }]


def test_merge_seguro_nunca_apaga_dado_existente_com_vazio():
    existente = {"nome": "Cliente A", "cidade": "Santos", "email": "a@x.com"}
    novo = {"nome": "Cliente A", "cidade": "", "email": None}

    plano = planejar_merge_sem_sobrescrita(existente, novo)

    assert plano["seguro"] is True
    assert plano["mesclado"]["cidade"] == "Santos"
    assert plano["mesclado"]["email"] == "a@x.com"
    assert plano["campos_preenchidos"] == []


def test_metadado_tecnico_nao_vira_conflito_de_negocio():
    existente = {"nome": "Cliente A", "pipeline": "ANTERIOR"}
    novo = {"nome": "Cliente A", "pipeline": "NOVO"}

    plano = planejar_merge_sem_sobrescrita(existente, novo)

    assert plano["seguro"] is True
    assert plano["conflitos"] == []
    assert plano["mesclado"]["pipeline"] == "ANTERIOR"
