from types import SimpleNamespace

import pytest

from services import ia_comercial_agente as agente


def _function_call(nome: str, argumentos: str, call_id: str):
    class FunctionCall:
        type = "function_call"
        name = nome
        arguments = argumentos

        def __init__(self):
            self.call_id = call_id

        def model_dump(self, exclude_none=True):
            return {
                "type": self.type,
                "name": self.name,
                "arguments": self.arguments,
                "call_id": self.call_id,
            }

    return FunctionCall()


def test_agente_nao_usa_teto_baixo_como_regra_funcional():
    assert agente.LIMITE_EMERGENCIAL_CICLOS >= 32
    assert agente.MAX_CICLOS_SEM_PROGRESSO <= 8
    assert "não existe uma cota de consultas ou fontes por resposta" in agente.INSTRUCOES_AGENTE.casefold()


def test_investigacao_multi_fonte_forca_sintese_final_com_evidencias(monkeypatch):
    chamadas_api = []
    respostas = [
        SimpleNamespace(id="r1", output=[_function_call("consultar_resumo_cti", "{}", "c1")], output_text="", usage=None),
        SimpleNamespace(id="r2", output=[_function_call("consultar_historico_cti", '{"termo":null,"limite":10}', "c2")], output_text="", usage=None),
        SimpleNamespace(id="r3", output=[_function_call("consultar_catalogo_produtos_cti", '{"termo":null}', "c3")], output_text="", usage=None),
        SimpleNamespace(id="r4", output=[_function_call("consultar_dominio_cti", '{"dominio":"clientes","termo":null,"limite":10}', "c4")], output_text="", usage=None),
        SimpleNamespace(id="r5", output=[], output_text="Relatório genérico de mercado que não usa os dados internos.", usage=None),
        SimpleNamespace(id="r6", output=[], output_text="Priorize o Cliente Alfa para a linha Trailer com base no histórico e nos dados CTI.", usage=None),
    ]

    class Responses:
        def create(self, **kwargs):
            chamadas_api.append(kwargs)
            return respostas[len(chamadas_api) - 1]

    class Client:
        responses = Responses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agente, "OpenAI", lambda **kwargs: Client())
    monkeypatch.setattr(agente, "_fontes_responses", lambda resposta: [])
    monkeypatch.setattr(
        agente,
        "_executar_ferramenta_cti",
        lambda nome, argumentos, usuario_id, tipo_usuario: {
            "ferramenta": nome,
            "dominio": argumentos.get("dominio"),
            "resultado": [{"cliente": "Cliente Alfa"}] if argumentos.get("dominio") == "clientes" else [],
        },
    )

    texto, metadados = agente.gerar_resposta_agente(
        mensagem="Cruze dados atuais do CTI, histórico, produtos e clientes.",
        historico=[],
        usuario_id="u1",
        tipo_usuario="ADMIN_MASTER",
    )

    assert texto == "Priorize o Cliente Alfa para a linha Trailer com base no histórico e nos dados CTI."
    assert len(chamadas_api) == 6
    assert "tools" not in chamadas_api[-1]
    assert any(
        isinstance(item, dict)
        and item.get("role") == "user"
        and "INSTRUÇÃO INTERNA DE SÍNTESE FINAL" in item.get("content", "")
        for item in chamadas_api[-1]["input"]
    )
    assert metadados["controle_loop"] == "progresso_evidencial"
    assert metadados["controle_sintese"] == "obrigatoria_multi_fonte"
    assert any(item.get("tipo") == "GATE_SINTESE" for item in metadados["ferramentas"])
    assert set(metadados["evidencias_atendidas"]) == {
        "cti_atual",
        "historico",
        "produtos",
        "clientes",
    }


def test_repeticao_sem_nova_evidencia_e_interrompida_por_estagnacao(monkeypatch):
    chamadas_api = []

    class Responses:
        def create(self, **kwargs):
            chamadas_api.append(kwargs)
            return SimpleNamespace(
                id=f"r{len(chamadas_api)}",
                output=[_function_call("consultar_resumo_cti", "{}", f"c{len(chamadas_api)}")],
                output_text="",
                usage=None,
            )

    class Client:
        responses = Responses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agente, "OpenAI", lambda **kwargs: Client())
    monkeypatch.setattr(agente, "_fontes_responses", lambda resposta: [])
    monkeypatch.setattr(
        agente,
        "_executar_ferramenta_cti",
        lambda nome, argumentos, usuario_id, tipo_usuario: {"ferramenta": nome},
    )
    monkeypatch.setattr(agente, "MAX_CICLOS_SEM_PROGRESSO", 2)

    with pytest.raises(agente.IAComercialOpenAIError) as exc:
        agente.gerar_resposta_agente(
            mensagem="Analise os dados atuais do CTI e o histórico.",
            historico=[],
            usuario_id="u1",
            tipo_usuario="ADMIN_MASTER",
        )

    assert exc.value.codigo == "AGENT_NO_PROGRESS"
    assert len(chamadas_api) < agente.LIMITE_EMERGENCIAL_CICLOS
