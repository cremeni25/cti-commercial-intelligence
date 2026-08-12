from services import ia_comercial_agente_crm as crm
from services import ia_comercial_planejamento as planejamento


def test_oportunidade_futura_em_plano_nao_forca_entidade_crm():
    pergunta = (
        "Com base na situação atual do pedido PED-20260804-A24FA6A7, monte um plano comercial prioritário. "
        "Separe o que deve ser feito agora, o que deve ser acompanhado depois e quais oportunidades futuras "
        "podem ser consideradas."
    )

    requeridas = crm._fontes_requeridas_crm(pergunta)

    assert "pedidos" in requeridas
    assert "oportunidades" not in requeridas
    assert planejamento._fontes_requeridas_semantica_ia007(pergunta) == requeridas - {"pedidos"}


def test_pipeline_explicito_continua_exigindo_entidade_oportunidade():
    pergunta = "Quais oportunidades abertas do pipeline estão vinculadas a este pedido e quais próximos passos recomenda?"

    requeridas = crm._fontes_requeridas_crm(pergunta)

    assert "oportunidades" in requeridas


def test_marcador_ia007_documenta_semantica_de_oportunidade_futura():
    assert "oportunidade futura" in planejamento._MARCADORES_OPORTUNIDADE_ANALITICA
    assert "pipeline" in planejamento._MARCADORES_OPORTUNIDADE_CRM
