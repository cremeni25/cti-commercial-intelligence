import json
from types import SimpleNamespace

from services import ia_comercial_sintese_factual as sintese


def test_dominios_nao_consultados_explicita_ausencias_sem_inferir_fatos():
    ausentes = sintese._dominios_nao_consultados({"anfir", "territorio"})

    assert "oportunidades" in ausentes
    assert "vendas" in ausentes
    assert "produtos" in ausentes
    assert "anfir" not in ausentes
    assert "territorio" not in ausentes


def test_instrucoes_proibem_pipeline_vendas_catalogo_ausencia_inferida_e_qualificadores_fortes():
    instrucoes = sintese.INSTRUCOES_SINTESE_FATUAL.casefold()

    assert "se oportunidades não foram consultadas" in instrucoes
    assert "se vendas não foram consultadas" in instrucoes
    assert "se produtos não foram consultados" in instrucoes
    assert "não faça afirmações positivas nem negativas" in instrucoes
    assert "relacionamento comercial ativo" in instrucoes
    assert "não use \"maioria\", \"predominante\"" in instrucoes
    assert "informe sempre contagens" in instrucoes
    assert "campo ausente não significa objeto ausente" in instrucoes
    assert "significa apenas \"não registrado/não informado na fonte\"" in instrucoes
    assert "por si só, não sustenta oportunidade de venda" in instrucoes
    assert "não frigorífico" in instrucoes


def test_reexecucao_usa_somente_ferramentas_cti_registradas(monkeypatch):
    chamadas = []

    def executar(nome, argumentos, usuario_id, tipo_usuario):
        chamadas.append((nome, argumentos, usuario_id, tipo_usuario))
        return {"ferramenta": nome, "resultado": [1]}

    monkeypatch.setattr(sintese, "_executar_ferramenta_cti", executar)

    metadados = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_territorio_cti",
                "argumentos": {"ddd": "011", "linha": "Trailer"},
            },
            {"tipo": "GATE_SINTESE", "evidencias": ["territorio"]},
            {
                "tipo": "CTI",
                "ferramenta": "consultar_territorio_cti",
                "argumentos": {"ddd": "011", "linha": "Trailer"},
            },
        ]
    }

    fontes = sintese._reexecutar_fontes_cti(metadados, "usuario-1", "ADMIN_MASTER")

    assert len(fontes) == 1
    assert chamadas == [
        (
            "consultar_territorio_cti",
            {"ddd": "011", "linha": "Trailer"},
            "usuario-1",
            "ADMIN_MASTER",
        )
    ]


def test_sintese_reconstruida_nao_recebe_resposta_preliminar_do_agente(monkeypatch):
    chamadas_api = []

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        sintese,
        "_reexecutar_fontes_cti",
        lambda metadados, usuario_id, tipo_usuario: [
            {
                "ferramenta": "consultar_territorio_cti",
                "argumentos": {"ddd": "011", "linha": "Trailer"},
                "resultado": {
                    "total_retornado": 18,
                    "resumo": {
                        "clientes": [{"valor": "PRODELOG", "quantidade": 8}],
                        "modelos_preenchidos": 0,
                    },
                },
            },
            {
                "ferramenta": "consultar_anfir_cti",
                "argumentos": {"ddd": "011", "linha": "Trailer"},
                "resultado": {"total_retornado": 18},
            },
        ],
    )

    resposta = SimpleNamespace(
        id="resp-sintese",
        output_text="Síntese factual limpa.",
        usage=SimpleNamespace(input_tokens=100, output_tokens=20),
    )

    class Responses:
        def create(self, **kwargs):
            chamadas_api.append(kwargs)
            return resposta

    class Client:
        responses = Responses()

    monkeypatch.setattr(sintese, "OpenAI", lambda **kwargs: Client())

    texto, metadados = sintese.sintetizar_fatos_execucao(
        pergunta_atual="Compare Trailer no DDD 011 com a ANFIR.",
        metadados={
            "evidencias_atendidas": ["anfir", "territorio"],
            "ferramentas": [],
        },
        usuario_id="usuario-1",
        tipo_usuario="ADMIN_MASTER",
    )

    assert texto == "Síntese factual limpa."
    assert len(chamadas_api) == 1
    assert chamadas_api[0]["store"] is False
    assert "tools" not in chamadas_api[0]
    payload = json.loads(chamadas_api[0]["input"][0]["content"])
    assert payload["PERGUNTA_ATUAL"] == "Compare Trailer no DDD 011 com a ANFIR."
    assert payload["EVIDENCIAS_ATENDIDAS"] == ["anfir", "territorio"]
    assert "oportunidades" in payload["DOMINIOS_NAO_CONSULTADOS"]
    assert "vendas" in payload["DOMINIOS_NAO_CONSULTADOS"]
    assert "produtos" in payload["DOMINIOS_NAO_CONSULTADOS"]
    assert "resposta preliminar" not in chamadas_api[0]["input"][0]["content"].casefold()
    assert metadados["controle_sintese_factual"] == "reconstruida_pergunta_e_fontes_execucao"
    assert metadados["sintese_factual_fontes_reexecutadas"] == 2


def test_sintese_com_web_fica_reservada_para_ia003():
    texto, metadados = sintese.sintetizar_fatos_execucao(
        pergunta_atual="Pesquise o mercado.",
        metadados={"evidencias_atendidas": ["web", "territorio"]},
        usuario_id="usuario-1",
        tipo_usuario="ADMIN_MASTER",
    )

    assert texto is None
    assert metadados["controle_sintese_factual"] == "adiada_para_ia003_com_web"
