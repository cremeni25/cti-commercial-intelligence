from pathlib import Path

from routers.ia_comercial_alvo_mapa_router import _localizar_auto, _separar_resposta


ROOT = Path(__file__).resolve().parents[2]
COMPONENTE = ROOT / "frontend" / "src" / "components" / "mapa" / "SinalDecisaoInterativo.tsx"


def test_separa_interpretacao_e_acao_naturais():
    interpretacao, acao = _separar_resposta(
        "INTERPRETAÇÃO: Cliente A concentra 5 unidades Direct Drive com concorrência TK. AÇÃO: Priorizar abordagem sobre a janela identificada."
    )
    assert "Cliente A" in interpretacao
    assert "Priorizar" in acao


def test_contexto_auto_localiza_alvo_autorizado_em_perdas_e_linha():
    alvo = {"cliente": "CLIENTE A", "responsavel": "MÔNICA", "unidades": 5}
    insights = {
        "perdas": {
            "direcionamento": {"alvos": [alvo]},
            "total_perdido": 20,
            "motivos": [{"nome": "Preço", "quantidade": 8}],
            "por_linha": [{"nome": "Direct Drive", "quantidade": 10}],
        },
        "linhas_2026": {
            "linhas": [{
                "codigo": "direct_drive",
                "nome": "Direct Drive",
                "total_2026": 30,
                "direcionamento": {"alvos": [alvo]},
                "composicao_marca": {"carrier": 10, "outras_marcas": 20, "marcas_concorrentes": []},
            }]
        },
        "regioes": [],
    }
    encontrado, contexto = _localizar_auto(insights, "CLIENTE A", "MÔNICA")
    assert encontrado["unidades"] == 5
    assert contexto["tipo"] == "MULTICONTEXTO"
    assert len(contexto["contextos"]) == 2


def test_frontend_busca_ia_real_e_nao_prioriza_frase_fixa_do_ciclo():
    fonte = COMPONENTE.read_text(encoding="utf-8")
    assert "getMapaAlvoInteligencia" in fonte
    assert "inteligencia?.interpretacao || leituraFactual" in fonte
    assert "inteligencia?.acao || acaoFactual" in fonte
    assert "alvo.leitura_ciclo ||" not in fonte
    assert "alvo.acao_ciclo ||" not in fonte
