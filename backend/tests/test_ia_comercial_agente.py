from types import SimpleNamespace

from services import ia_comercial_agente as agente


def test_catalogo_agente_combina_web_e_ferramentas_cti():
    ferramentas = agente.ferramentas_agente()
    tipos = [item["type"] for item in ferramentas]
    nomes = {item.get("name") for item in ferramentas if item.get("type") == "function"}

    assert "web_search" in tipos
    assert nomes == {
        "consultar_resumo_cti",
        "consultar_dominio_cti",
        "consultar_historico_cti",
    }


def test_entrada_inicial_preserva_contexto_conversacional_recente():
    historico = [
        {"role": "user", "content": "Analise o cliente Alfa."},
        {"role": "assistant", "content": "Vou considerar os dados disponíveis."},
    ]

    entrada = agente._entrada_inicial("Agora compare com o mercado.", historico)

    assert entrada == [
        {"role": "user", "content": "Analise o cliente Alfa."},
        {"role": "assistant", "content": "Vou considerar os dados disponíveis."},
        {"role": "user", "content": "Agora compare com o mercado."},
    ]


def test_consultar_resumo_cti_respeita_resultado_autorizado(monkeypatch):
    monkeypatch.setattr(
        agente,
        "contexto_comercial",
        lambda usuario_id, tipo_usuario: {
            "escopo": "usuario_autorizado",
            "quantidades": {"oportunidades": 4},
            "valores": {"pedidos_em_curso": 150000.0},
            "fontes_disponiveis": ["CRM"],
        },
    )

    resultado = agente._executar_ferramenta_cti(
        "consultar_resumo_cti",
        {},
        "usuario-1",
        "VENDEDOR",
    )

    assert resultado["escopo"] == "usuario_autorizado"
    assert resultado["quantidades"]["oportunidades"] == 4
    assert resultado["valores"]["pedidos_em_curso"] == 150000.0


def test_loop_agente_store_false_reenvia_contexto_sem_previous_response_id(monkeypatch):
    chamadas_api = []

    class FunctionCall:
        type = "function_call"
        name = "consultar_resumo_cti"
        arguments = "{}"
        call_id = "call-1"

        def model_dump(self, exclude_none=True):
            return {
                "type": self.type,
                "name": self.name,
                "arguments": self.arguments,
                "call_id": self.call_id,
            }

    primeira = SimpleNamespace(
        id="resp-1",
        output=[FunctionCall()],
        output_text="",
        usage=None,
    )
    segunda = SimpleNamespace(
        id="resp-2",
        output=[],
        output_text="Análise concluída.",
        usage=None,
    )

    class Responses:
        def create(self, **kwargs):
            chamadas_api.append(kwargs)
            return primeira if len(chamadas_api) == 1 else segunda

    class Client:
        responses = Responses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agente, "OpenAI", lambda **kwargs: Client())
    monkeypatch.setattr(
        agente,
        "_executar_ferramenta_cti",
        lambda nome, argumentos, usuario_id, tipo_usuario: {
            "ferramenta": nome,
            "quantidades": {"oportunidades": 2},
        },
    )
    monkeypatch.setattr(agente, "_fontes_responses", lambda resposta: [])

    texto, metadados = agente.gerar_resposta_agente(
        mensagem="Analise a situação comercial atual.",
        historico=[],
        usuario_id="usuario-1",
        tipo_usuario="ADMIN_MASTER",
    )

    assert texto == "Análise concluída."
    assert len(chamadas_api) == 2
    assert chamadas_api[0]["store"] is False
    assert chamadas_api[1]["store"] is False
    assert "previous_response_id" not in chamadas_api[1]
    assert any(
        item.get("type") == "function_call"
        for item in chamadas_api[1]["input"]
        if isinstance(item, dict)
    )
    assert any(
        item.get("type") == "function_call_output" and item.get("call_id") == "call-1"
        for item in chamadas_api[1]["input"]
        if isinstance(item, dict)
    )
    assert metadados["arquitetura"] == "agente_orquestrador"
