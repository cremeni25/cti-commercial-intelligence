from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "ia_comercial_mapa_router.py"
API = ROOT / "backend" / "routers" / "cti_api_router.py"
MAPA = ROOT / "frontend" / "src" / "app" / "mapa-estrategico" / "page.tsx"
SERVICE = ROOT / "frontend" / "src" / "services" / "mapa-equipe-api.ts"


def test_endpoint_contextual_permanece_read_only_e_sem_persistencia():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "gerar_resposta_agente" in fonte
    assert '@router.get("/inteligencia")' in fonte
    assert '@router.post("/inteligencia/perguntar")' in fonte
    assert "cti_ia_conversas" not in fonte
    assert "cti_ia_mensagens" not in fonte
    assert '"somente_leitura": True' in fonte
    assert '"persistido": False' in fonte


def test_selecao_individual_usa_escopo_do_responsavel_analisado():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "_perfil_analise" in fonte
    assert "selecionado_id" in fonte
    assert "usuario_analise_id" in fonte
    assert "gerar_resposta_agente(" in fonte
    assert "visao_equipe(responsavel_id=responsavel_id, usuario=usuario)" in fonte


def test_continuidade_contextual_permanece_disponivel_para_uso_controlado():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "PerguntaContextual" in fonte
    assert "TurnoContextual" in fonte
    assert "payload.historico[-8:]" in fonte
    assert "MESMO contexto selecionado" in fonte
    assert "histórico transitório" in fonte
    assert "SNAPSHOT ATUAL DA SELEÇÃO" in fonte
    assert "ANFIR representa mercado realizado/referência e nunca deve virar oportunidade automática" in fonte
    assert "CRM representa negócios atuais em andamento" in fonte


def test_router_e_servico_mantem_endpoint_sem_forcar_ia_na_tela_principal():
    api = API.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    mapa = MAPA.read_text(encoding="utf-8")
    assert "ia_comercial_mapa_router" in api
    assert "router.include_router(ia_comercial_mapa_router)" in api
    assert "getMapaEquipeInteligencia" in service
    assert "perguntarMapaEquipeInteligencia" in service
    assert "crm-seguro/mapa-equipe/inteligencia/perguntar" in service
    assert "getMapaEquipeInteligencia" not in mapa
    assert "perguntarMapaEquipeInteligencia" not in mapa
    assert "historicoContextual" not in mapa


def test_mapa_prioriza_graficos_e_acao_comercial_em_2026():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Como o mercado está dividido" in mapa
    assert "Composição por linha" in mapa
    assert "Como estão os negócios em andamento" in mapa
    assert "GraficoLinha" in mapa
    assert "Leitura comercial" in mapa
    assert "O que fazer" in mapa
    assert "Perdas comerciais · 2026" in mapa
    assert "Evolução por linha · 2026" in mapa
    assert "Histórico comercial 2023–2026" not in mapa
    assert "Dados de apoio e auditoria" in mapa


def test_mapa_nao_exibe_analise_web_enciclopedica_ou_novo_atalho_de_ia():
    mapa = MAPA.read_text(encoding="utf-8")
    assert "Fatos externos verificados" not in mapa
    assert "https://anfir" not in mapa
    assert "Aprofundar na IA" not in mapa
    assert "aprofundarNaIa" not in mapa
    assert "/ia-comercial?prompt=" not in mapa
    assert "Contexto utilizado" not in mapa
