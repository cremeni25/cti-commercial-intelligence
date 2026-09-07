from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "ia_comercial_mapa_router.py"
API = ROOT / "backend" / "routers" / "cti_api_router.py"
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"
SERVICE = ROOT / "frontend" / "src" / "services" / "mapa-equipe-api.ts"


def test_mapa_chama_ia_comercial_real_sem_persistir_conversa():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "gerar_resposta_agente" in fonte
    assert '@router.get("/inteligencia")' in fonte
    assert '@router.post("/inteligencia/perguntar")' in fonte
    assert "cti_ia_conversas" not in fonte
    assert "cti_ia_mensagens" not in fonte
    assert '"somente_leitura": True' in fonte
    assert '"persistido": False' in fonte


def test_prompt_exige_linguagem_natural_e_nao_formato_mockado():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "linguagem comercial natural" in fonte
    assert "sem tabela" in fonte.lower()
    assert "quantidade fixa de insights" in fonte.lower()
    assert "frases prontas" in fonte.lower()
    assert "Não repita os indicadores do painel" in fonte


def test_selecao_individual_usa_escopo_do_responsavel_analisado():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "_perfil_analise" in fonte
    assert "selecionado_id" in fonte
    assert "usuario_analise_id" in fonte
    assert "gerar_resposta_agente(" in fonte
    assert "visao_equipe(responsavel_id=responsavel_id, usuario=usuario)" in fonte


def test_continuidade_conversacional_e_transitoria_e_revalida_contexto():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "PerguntaContextual" in fonte
    assert "TurnoContextual" in fonte
    assert "payload.historico[-8:]" in fonte
    assert "MESMO contexto selecionado" in fonte
    assert "histórico transitório" in fonte
    assert "SNAPSHOT ATUAL DA SELEÇÃO" in fonte
    assert "ANFIR representa mercado realizado/referência e nunca deve virar oportunidade automática" in fonte
    assert "CRM representa negócios atuais em andamento" in fonte


def test_router_e_frontend_estao_integrados():
    api = API.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    mapa = MAPA.read_text(encoding="utf-8")
    assert "ia_comercial_mapa_router" in api
    assert "router.include_router(ia_comercial_mapa_router)" in api
    assert "getMapaEquipeInteligencia" in service
    assert "perguntarMapaEquipeInteligencia" in service
    assert "crm-seguro/mapa-equipe/inteligencia/perguntar" in service
    assert "perguntarMapaEquipeInteligencia" in mapa
    assert "historicoContextual" in mapa


def test_proveniencia_contextual_e_canonica_e_discreta():
    fonte = ROUTER.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    mapa = MAPA.read_text(encoding="utf-8")
    assert '"fontes_contextuais": _fontes_contextuais(visao)' in fonte
    assert "TERRITORIO_RESPONSAVEL" in fonte
    assert "ANFIR_2026" in fonte
    assert "HISTORICO_FUNIL_2026" in fonte
    assert "CRM_ATUAL" in fonte
    assert "FonteContextual" in service
    assert 'role: "user" | "assistant"' in service
    assert "Contexto utilizado" in mapa
    assert "fontesContextuais.map" in mapa
    assert "novosTurnos: TurnoContextual[]" in mapa


def test_mapa_remove_abas_redundantes_e_prioriza_sinais_de_decisao():
    mapa = MAPA.read_text(encoding="utf-8")
    assert 'label: "Mercado"' not in mapa
    assert 'label: "Equipe / responsável"' not in mapa
    assert 'type Visao = "executiva" | "crm" | "historico"' not in mapa
    assert "const visoes" not in mapa
    assert "setVisao" not in mapa
    assert "Sinais de decisão" in mapa
    assert "Onde a seleção pede atenção" in mapa
    assert "Lacuna de conhecimento comercial" in mapa
    assert "não oportunidade automática" in mapa


def test_inteligencia_comercial_permanece_embutida_sem_novo_atalho_de_ia():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Aprofundar na IA" not in mapa
    assert "aprofundarNaIa" not in mapa
    assert "/ia-comercial?prompt=" not in mapa
    assert "Interpretação contextual" in mapa
    assert "Pergunte sobre a leitura desta seleção" in mapa
    assert "Contexto utilizado" in mapa
