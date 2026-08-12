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
    assert "só use dimensões factuais que aparecem em resumo_relevante" in instrucoes


def test_evidencias_permitidas_excluem_fonte_extra_nao_requerida():
    metadados = {
        "evidencias_requeridas": ["anfir", "territorio"],
        "evidencias_atendidas": ["anfir", "territorio", "produtos"],
    }

    assert sintese._evidencias_permitidas_sintese(metadados) == {"anfir", "territorio"}


def test_reexecucao_ignora_catalogo_extra_nao_requerido(monkeypatch):
    chamadas = []

    def executar(nome, argumentos, usuario_id, tipo_usuario):
        chamadas.append(nome)
        return {
            "fonte": "cti_anfir",
            "visao": "territorio" if "territorio" in nome else "anfir_historico",
            "total_encontrado": 18,
            "filtros_aplicados": {"ddd": "011", "linha": "TR"},
            "resumo": {
                "total_registros": 18,
                "total_clientes": 4,
                "cobertura": {"com_modelo": 0, "sem_modelo": 18},
                "ranking_clientes": [],
                "ranking_modelos": [],
                "ranking_ddds": [],
                "ranking_estados": [],
                "ranking_cidades": [],
            },
        }

    monkeypatch.setattr(sintese, "_executar_ferramenta_cti", executar)
    metadados = {
        "evidencias_requeridas": ["anfir", "territorio"],
        "evidencias_atendidas": ["anfir", "territorio", "produtos"],
        "ferramentas": [
            {"tipo": "CTI", "ferramenta": "consultar_territorio_cti", "argumentos": {"ddd": "011"}},
            {"tipo": "CTI", "ferramenta": "consultar_catalogo_produtos_cti", "argumentos": {"termo": "Trailer"}},
            {"tipo": "CTI", "ferramenta": "consultar_anfir_cti", "argumentos": {"ddd": "011"}},
        ],
    }

    fontes = sintese._reexecutar_fontes_cti(
        metadados,
        "usuario-1",
        "ADMIN_MASTER",
        pergunta_atual="Mostre clientes, modelos e concentração territorial.",
    )

    assert chamadas == ["consultar_territorio_cti", "consultar_anfir_cti"]
    assert all(item["ferramenta"] != "consultar_catalogo_produtos_cti" for item in fontes)


def test_resumo_territorial_remove_status_fabricante_e_implementadora_quando_nao_pedidos():
    resultado = {
        "total_encontrado": 18,
        "resumo": {
            "total_registros": 18,
            "total_clientes": 4,
            "cobertura": {"com_modelo": 0, "sem_modelo": 18},
            "ranking_clientes": [{"valor": "PRODELOG", "registros": 8}],
            "ranking_modelos": [],
            "ranking_ddds": [{"valor": "011", "registros": 18}],
            "ranking_estados": [{"valor": "SP", "registros": 18}],
            "ranking_cidades": [{"valor": "JUNDIAI", "registros": 8}],
            "ranking_implementadoras": [{"valor": "IBIPORA", "registros": 8}],
            "ranking_fabricantes_equipamento": [{"valor": "CARRRIER", "registros": 8}],
        },
        "resultado": [{"status": "APROVADO", "fabricante_equipamento": "CARRRIER"}],
    }

    reduzido = sintese._reduzir_resultado_para_sintese(
        "consultar_anfir_cti",
        resultado,
        "Mostre clientes, modelos e concentração territorial no DDD 011.",
    )
    resumo = reduzido["RESUMO_RELEVANTE"]

    assert resumo["total_registros"] == 18
    assert resumo["cobertura_modelos"] == {"com_modelo": 0, "sem_modelo": 18}
    assert "ranking_clientes" in resumo
    assert "ranking_cidades" in resumo
    assert "ranking_implementadoras" not in resumo
    assert "ranking_fabricantes_equipamento" not in resumo
    assert "resultado" not in reduzido
    assert "status" not in json.dumps(reduzido, ensure_ascii=False).casefold()


def test_reexecucao_usa_somente_ferramentas_cti_registradas(monkeypatch):
    chamadas = []

    def executar(nome, argumentos, usuario_id, tipo_usuario):
        chamadas.append((nome, argumentos, usuario_id, tipo_usuario))
        return {
            "fonte": "cti_anfir",
            "visao": "territorio",
            "total_encontrado": 1,
            "resumo": {"total_registros": 1, "total_clientes": 1, "cobertura": {}},
        }

    monkeypatch.setattr(sintese, "_executar_ferramenta_cti", executar)

    metadados = {
        "evidencias_requeridas": ["territorio"],
        "evidencias_atendidas": ["territorio"],
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
        ],
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
        lambda metadados, usuario_id, tipo_usuario, pergunta_atual="": [
            {
                "ferramenta": "consultar_territorio_cti",
                "argumentos": {"ddd": "011", "linha": "Trailer"},
                "resultado": {"RESUMO_RELEVANTE": {"total_registros": 18}},
            },
            {
                "ferramenta": "consultar_anfir_cti",
                "argumentos": {"ddd": "011", "linha": "Trailer"},
                "resultado": {"RESUMO_RELEVANTE": {"total_registros": 18}},
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
            "evidencias_requeridas": ["anfir", "territorio"],
            "evidencias_atendidas": ["anfir", "territorio", "produtos"],
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
    assert payload["EVIDENCIAS_REQUERIDAS"] == ["anfir", "territorio"]
    assert "oportunidades" in payload["DOMINIOS_NAO_CONSULTADOS"]
    assert "vendas" in payload["DOMINIOS_NAO_CONSULTADOS"]
    assert "produtos" in payload["DOMINIOS_NAO_CONSULTADOS"]
    assert "resposta preliminar" not in chamadas_api[0]["input"][0]["content"].casefold()
    assert metadados["controle_sintese_factual"] == "reconstruida_pergunta_fontes_e_dimensoes_requeridas"
    assert metadados["sintese_factual_fontes_reexecutadas"] == 2
    assert metadados["sintese_factual_evidencias_permitidas"] == ["anfir", "territorio"]


def test_sintese_com_web_fica_reservada_para_ia003():
    texto, metadados = sintese.sintetizar_fatos_execucao(
        pergunta_atual="Pesquise o mercado.",
        metadados={
            "evidencias_requeridas": ["web", "territorio"],
            "evidencias_atendidas": ["web", "territorio"],
        },
        usuario_id="usuario-1",
        tipo_usuario="ADMIN_MASTER",
    )

    assert texto is None
    assert metadados["controle_sintese_factual"] == "adiada_para_ia003_com_web"
