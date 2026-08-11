from services import ia_comercial_agente_crm as agente_crm
from services import ia_comercial_dados_semanticos as dados
from services import ia_comercial_sintese_crm as sintese_crm


def test_fontes_requeridas_crm_operacional_sao_deterministicas():
    assert agente_crm._fontes_requeridas_crm("Qual o acompanhamento dos pedidos?") == {"pedidos"}
    assert agente_crm._fontes_requeridas_crm("Quais propostas foram aceitas e viraram pedido?") == {"propostas", "pedidos"}
    assert agente_crm._fontes_requeridas_crm("Mostre as últimas visitas e atividades") == {"atividades"}


def test_evidencias_presentes_reconhecem_dominios_crm():
    rastreio = [
        {"tipo": "CTI", "ferramenta": "consultar_dominio_cti", "argumentos": {"dominio": "propostas"}},
        {"tipo": "CTI", "ferramenta": "consultar_dominio_cti", "argumentos": {"dominio": "pedidos"}},
        {"tipo": "CTI", "ferramenta": "consultar_dominio_cti", "argumentos": {"dominio": "atividades"}},
    ]
    presentes = agente_crm._evidencias_presentes_crm(rastreio, [])
    assert {"propostas", "pedidos", "atividades"}.issubset(presentes)


def test_semantica_ciclo_pedido_define_proxima_etapa_e_pendencia():
    pedido = {
        "status_ciclo": "CARRIER",
        "status_envio_carrier": "ENVIADO",
        "enviado_carrier_em": "2026-08-03T18:53:57Z",
        "carrier_confirmado_em": "2026-08-03T18:53:57Z",
    }
    semantica = dados._semantica_ciclo_pedido(pedido)
    assert semantica["etapa_atual"] == "CARRIER"
    assert semantica["proxima_etapa"] == "FATURADO"
    assert semantica["pendencias_operacionais"] == [
        "registrar faturamento com número da NF e número de série constante na NF"
    ]
    assert semantica["inconsistencias_qualidade"] == []


def test_semantica_ciclo_pedido_nao_permite_saltar_carrier():
    pedido = {"status_ciclo": "PEDIDO", "status_envio_carrier": "NAO_ENVIADO"}
    semantica = dados._semantica_ciclo_pedido(pedido)
    assert semantica["proxima_etapa"] == "CARRIER"
    assert "enviar pedido à Carrier" in semantica["pendencias_operacionais"][0]


def test_semantica_proposta_aceita_sem_pedido_indica_pendencia():
    proposta = {"status": "APROVADA", "aceita_em": "2026-08-04T10:00:00Z"}
    semantica = dados._semantica_proposta(proposta, None, [])
    assert semantica["aceita"] is True
    assert semantica["pedido_gerado"] is False
    assert semantica["pendencias_operacionais"] == ["gerar pedido a partir da proposta aceita"]


def test_semantica_proposta_pedido_sem_aceite_sinaliza_inconsistencia():
    proposta = {"status": "EMITIDA"}
    semantica = dados._semantica_proposta(proposta, None, [{"id": "pedido-1"}])
    assert "existe pedido vinculado sem evidência de aceite da proposta" in semantica["inconsistencias_qualidade"]


def test_sintese_crm_preserva_semantica_backend_sem_reconstruir():
    texto, metadados = sintese_crm.sintetizar_fatos_execucao(
        "Qual a situação dos pedidos?",
        {"evidencias_atendidas": ["pedidos"]},
        "usuario",
        "ADMIN_MASTER",
    )
    assert texto is None
    assert metadados["controle_sintese_factual"] == "crm_operacional_semantico_preservado"
    assert metadados["crm_evidencias"] == ["pedidos"]
