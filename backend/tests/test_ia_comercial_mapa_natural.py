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
    assert "cti_ia_conversas" not in fonte
    assert "cti_ia_mensagens" not in fonte
    assert '"somente_leitura": True' in fonte


def test_prompt_exige_linguagem_natural_e_nao_formato_mockado():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "linguagem natural" in fonte
    assert "não use tabela" in fonte.lower()
    assert "não imponha quantidade fixa de insights" in fonte.lower()
    assert "não siga frases prontas" in fonte.lower()
    assert "Não repita os indicadores do painel" in fonte


def test_selecao_individual_usa_escopo_do_responsavel_analisado():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "_perfil_analise" in fonte
    assert "selecionado_id" in fonte
    assert "usuario_analise_id" in fonte
    assert "gerar_resposta_agente(" in fonte


def test_router_e_frontend_estao_integrados():
    api = API.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    mapa = MAPA.read_text(encoding="utf-8")
    assert "ia_comercial_mapa_router" in api
    assert "router.include_router(ia_comercial_mapa_router)" in api
    assert "getMapaEquipeInteligencia" in service
    assert "crm-seguro/mapa-equipe/inteligencia" in service
    assert "getMapaEquipeInteligencia" in mapa


def test_mapa_remove_leitura_executiva_de_frases_fixas_e_abas_redundantes():
    mapa = MAPA.read_text(encoding="utf-8")
    assert 'label: "Mercado"' not in mapa
    assert 'label: "Equipe / responsável"' not in mapa
    assert 'type Visao = "executiva" | "crm" | "historico"' in mapa
    assert "do Mercado Real ainda está fora da análise selecionada" not in mapa
    assert "negociação(ões) ativa(s)" not in mapa
    assert "O que os dados estão mostrando" in mapa


def test_inteligencia_comercial_nao_cria_novo_atalho_ou_botao_de_ia():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Aprofundar na IA" not in mapa
    assert "aprofundarNaIa" not in mapa
    assert "/ia-comercial?prompt=" not in mapa
    assert "Leitura contextual" in mapa
