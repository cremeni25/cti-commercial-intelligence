from services import ia_comercial_agente_crm as crm


def test_oportunidades_futuras_de_plano_nao_viram_entidade_crm():
    pergunta = (
        "Com base na situação atual do pedido PED-20260804-A24FA6A7, monte um plano comercial prioritário "
        "para conduzi-lo corretamente daqui em diante. Separe o que deve ser feito agora, o que deve ser "
        "acompanhado depois e quais oportunidades futuras podem ser consideradas. Justifique a ordem das ações."
    )

    requeridas = crm._fontes_requeridas_crm(pergunta)

    assert "pedidos" in requeridas
    assert "oportunidades" not in requeridas


def test_oportunidade_crm_explicita_continua_exigindo_dominio_oportunidades():
    requeridas = crm._fontes_requeridas_crm(
        "No pedido PED-20260804-A24FA6A7, verifique as oportunidades vinculadas no CRM e o status da oportunidade."
    )

    assert "pedidos" in requeridas
    assert "oportunidades" in requeridas
