from core.ingestion_promotion import selecionar_itens_promocao, validar_lote


def _item(i, entidade, natureza, status="PRONTO_PROMOCAO"):
    return {
        "id": f"item-{i}",
        "indice_semantico": i,
        "entidade_sugerida": entidade,
        "natureza_canonica": natureza,
        "status_item": status,
        "dados_normalizados": {"nome": f"Registro {i}"},
    }


def test_lote_misto_exige_natureza_alvo():
    rec = {"status": "PRONTO_PROMOCAO", "dominio_alvo": "CRM_COMERCIAL"}
    itens = [
        _item(1, "CLIENTE", "CRM_CADASTRAL"),
        _item(2, "OPORTUNIDADE", "FUNIL_COMERCIAL"),
    ]
    resultado = validar_lote(rec, itens)
    assert resultado["aprovado"] is False
    assert resultado["bloqueios"][0]["motivo"] == "LOTE_MISTO_REQUER_NATUREZA_ALVO"


def test_selecao_por_natureza_isola_subconjunto_sem_fusao():
    itens = [
        _item(1, "CLIENTE", "CRM_CADASTRAL"),
        _item(2, "OPORTUNIDADE", "FUNIL_COMERCIAL"),
        _item(3, "CLIENTE", "CRM_CADASTRAL"),
    ]
    selecionados = selecionar_itens_promocao(itens, "CRM_CADASTRAL")
    assert [i["id"] for i in selecionados] == ["item-1", "item-3"]
    assert all(i["natureza_canonica"] == "CRM_CADASTRAL" for i in selecionados)


def test_subconjunto_cliente_pode_ser_validado_sem_promover_funil():
    rec = {"status": "PRONTO_PROMOCAO", "dominio_alvo": "CRM_COMERCIAL"}
    itens = [
        _item(1, "CLIENTE", "CRM_CADASTRAL"),
        _item(2, "OPORTUNIDADE", "FUNIL_COMERCIAL"),
    ]
    resultado = validar_lote(rec, itens, natureza_alvo="CRM_CADASTRAL")
    assert resultado["aprovado"] is True
    assert resultado["total"] == 1
    assert resultado["natureza_alvo"] == "CRM_CADASTRAL"


def test_natureza_inexistente_nao_passa():
    rec = {"status": "PRONTO_PROMOCAO", "dominio_alvo": "CRM_COMERCIAL"}
    itens = [_item(1, "CLIENTE", "CRM_CADASTRAL")]
    resultado = validar_lote(rec, itens, natureza_alvo="FUNIL_COMERCIAL")
    assert resultado["aprovado"] is False
    assert resultado["bloqueios"][0]["motivo"] == "NATUREZA_SEM_ITENS"


def test_promocao_parcial_pode_continuar_noutra_natureza():
    rec = {"status": "PROMOCAO_PARCIAL", "dominio_alvo": "CRM_COMERCIAL"}
    itens = [_item(1, "CLIENTE", "CRM_CADASTRAL")]
    resultado = validar_lote(rec, itens, natureza_alvo="CRM_CADASTRAL")
    assert resultado["aprovado"] is True
