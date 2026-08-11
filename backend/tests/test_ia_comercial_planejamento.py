from types import SimpleNamespace

from services import ia_comercial_planejamento as planejamento
from services.ia_comercial_planejamento import requer_planejamento, validar_plano


def auditoria_base():
    return {
        "afirmacoes": [
            {
                "id": "A1",
                "tipo": "FATO_CTI",
                "texto": "O pedido PED-001 está na etapa PEDIDO e a próxima etapa é CARRIER.",
                "status_rastreabilidade": "RASTREAVEL",
            },
            {
                "id": "A2",
                "tipo": "FATO_CTI",
                "texto": "A oportunidade vinculada está em status GANHO.",
                "status_rastreabilidade": "RASTREAVEL",
            },
            {
                "id": "A3",
                "tipo": "INFERENCIA_RECOMENDACAO",
                "texto": "O portfólio atual pode exigir atualização.",
                "status_rastreabilidade": "BASE_PARCIAL",
                "premissas_fatuais_nao_sustentadas": ["produtos"],
            },
            {
                "id": "A4",
                "tipo": "FATO_CTI",
                "texto": "Há uma venda recente.",
                "status_rastreabilidade": "SEM_EVIDENCIA_EXPLICITA",
            },
        ],
        "evidencias_atendidas": ["pedidos"],
    }


def test_detecta_intencao_de_planejamento():
    assert requer_planejamento("Qual a prioridade e o que devo fazer agora?") is True
    assert requer_planejamento("Qual é a etapa atual do pedido?") is False


def test_plano_remove_fundamento_sem_evidencia():
    plano = validar_plano(
        {
            "objetivo": "Resolver o pedido.",
            "acoes": [
                {
                    "acao": "Usar a venda recente como argumento.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A4"],
                }
            ],
        },
        auditoria_base(),
    )
    assert plano["acoes"] == []


def test_plano_nao_manda_avancar_oportunidade_ganha():
    plano = validar_plano(
        {
            "objetivo": "Organizar próximos passos.",
            "acoes": [
                {
                    "acao": "Avançar a oportunidade para a próxima etapa do pipeline.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A2"],
                },
                {
                    "acao": "Priorizar o envio do pedido à Carrier.",
                    "prioridade": "ALTA",
                    "horizonte": "IMEDIATO",
                    "fundamentos": ["A1"],
                },
            ],
        },
        auditoria_base(),
    )
    assert len(plano["acoes"]) == 1
    assert "pedido" in plano["acoes"][0]["acao"].casefold()
    assert plano["oportunidade_encerrada_detectada"] is True


def test_base_parcial_e_propagada_para_acao():
    plano = validar_plano(
        {
            "objetivo": "Planejar evolução comercial.",
            "acoes": [
                {
                    "acao": "Avaliar atualização do portfólio.",
                    "prioridade": "MEDIA",
                    "horizonte": "MEDIO_PRAZO",
                    "fundamentos": ["A3"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["qualificacao_evidencial"] == "BASE_PARCIAL"
    assert acao["lacunas_evidenciais"] == ["produtos"]


def test_ordem_prioridade_e_horizonte_sao_normalizados():
    plano = validar_plano(
        {
            "objetivo": "Executar.",
            "acoes": [
                {
                    "ordem": 99,
                    "acao": "Enviar o pedido à Carrier.",
                    "prioridade": "URGENTE",
                    "horizonte": "AMANHA",
                    "fundamentos": ["A1"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["ordem"] == 1
    assert acao["prioridade"] == "MEDIA"
    assert acao["horizonte"] == "CURTO_PRAZO"


def test_acao_regional_sem_territorio_fica_base_parcial():
    plano = validar_plano(
        {
            "objetivo": "Expandir comercialmente.",
            "acoes": [
                {
                    "acao": "Prospectar potenciais clientes na região de São Bernardo do Campo.",
                    "prioridade": "BAIXA",
                    "horizonte": "MEDIO_PRAZO",
                    "fundamentos": ["A1"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["qualificacao_evidencial"] == "BASE_PARCIAL"
    assert "territorio" in acao["lacunas_evidenciais"]
    assert "demanda_comercial_futura" in acao["lacunas_evidenciais"]


def test_acao_digital_sustentavel_sem_web_e_produtos_fica_base_parcial():
    plano = validar_plano(
        {
            "objetivo": "Preparar oferta futura.",
            "acoes": [
                {
                    "acao": "Explorar parcerias tecnológicas para oferta integrada de soluções digitais e sustentáveis.",
                    "prioridade": "BAIXA",
                    "horizonte": "MEDIO_PRAZO",
                    "fundamentos": ["A1"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["qualificacao_evidencial"] == "BASE_PARCIAL"
    assert set(acao["lacunas_evidenciais"]) == {"web", "produtos"}


def test_tecnologias_emergentes_e_parcerias_comerciais_sem_fontes_ficam_parciais():
    plano = validar_plano(
        {
            "objetivo": "Preparar expansão futura.",
            "acoes": [
                {
                    "acao": (
                        "Prospectar novas vendas com clientes da região e estudar possibilidades futuras de "
                        "incorporação de tecnologias emergentes e parcerias comerciais para competitividade."
                    ),
                    "prioridade": "BAIXA",
                    "horizonte": "MEDIO_PRAZO",
                    "fundamentos": ["A1"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["qualificacao_evidencial"] == "BASE_PARCIAL"
    assert set(acao["lacunas_evidenciais"]) == {
        "territorio",
        "produtos",
        "web",
        "demanda_comercial_futura",
    }


def test_prospectar_nova_venda_com_cliente_do_pedido_nao_vira_evidencia_completa():
    plano = validar_plano(
        {
            "objetivo": "Preparar relacionamento futuro.",
            "acoes": [
                {
                    "acao": "Prospectar novas vendas com o cliente ABC CARGAS LTDA à medida que o relacionamento comercial se consolida.",
                    "prioridade": "MEDIA",
                    "horizonte": "MEDIO_PRAZO",
                    "fundamentos": ["A1"],
                }
            ],
        },
        auditoria_base(),
    )
    acao = plano["acoes"][0]
    assert acao["qualificacao_evidencial"] == "BASE_PARCIAL"
    assert acao["lacunas_evidenciais"] == ["demanda_comercial_futura"]


def test_fontes_territorio_produtos_web_nao_provam_demanda_futura():
    auditoria = auditoria_base()
    auditoria["evidencias_atendidas"] = ["pedidos", "territorio", "produtos", "web"]
    plano = validar_plano(
        {
            "objetivo": "Expandir.",
            "acoes": [
                {
                    "acao": "Prospectar potenciais clientes na região e explorar oferta integrada de soluções digitais e sustentáveis.",
                    "prioridade": "BAIXA",
                    "horizonte": "MEDIO_PRAZO",
                    "fundamentos": ["A1"],
                }
            ],
        },
        auditoria,
    )
    acao = plano["acoes"][0]
    assert acao["qualificacao_evidencial"] == "BASE_PARCIAL"
    assert acao["lacunas_evidenciais"] == ["demanda_comercial_futura"]


def test_resposta_final_remove_texto_livre_que_nao_passou_pela_validacao(monkeypatch):
    resposta_modelo = {
        "objetivo": "Conduzir o pedido.",
        "acoes": [
            {
                "acao": "Enviar o pedido à Carrier.",
                "prioridade": "ALTA",
                "horizonte": "IMEDIATO",
                "fundamentos": ["A1"],
                "dependencias": [],
                "riscos": [],
                "resultado_esperado": "Avançar o ciclo do pedido.",
            },
            {
                "acao": "Criar parceria tecnológica sem evidência.",
                "prioridade": "MEDIA",
                "horizonte": "MEDIO_PRAZO",
                "fundamentos": ["A4"],
                "dependencias": [],
                "riscos": [],
                "resultado_esperado": "Nova oferta.",
            },
        ],
    }

    class Responses:
        def create(self, **kwargs):
            import json
            return SimpleNamespace(output_text=json.dumps(resposta_modelo, ensure_ascii=False))

    class Client:
        responses = Responses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(planejamento, "OpenAI", lambda **kwargs: Client())

    metadados = {
        "auditoria_evidencial": auditoria_base(),
    }
    texto, meta = planejamento.construir_planejamento_comercial(
        "Monte um plano e diga o que fazer.",
        "Texto livre anterior com parceria tecnológica sem evidência.",
        metadados,
    )

    assert texto.startswith("PLANO COMERCIAL ESTRUTURADO")
    assert "Texto livre anterior" not in texto
    assert "parceria tecnológica" not in texto
    assert "Enviar o pedido à Carrier" in texto
    assert meta["controle_resposta_planejamento"] == "somente_plano_validado_sem_texto_livre_previo"
