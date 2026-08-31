from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PIPELINE_PAGE = ROOT / "frontend" / "src" / "app" / "pipeline" / "page.tsx"


def test_pipeline_nao_exclui_negociacao_ativa_por_data_de_previsao():
    source = PIPELINE_PAGE.read_text(encoding="utf-8")
    assert "if(!item.encerrada)return true" in source
    assert "data_fechamento_prevista" in source


def test_previsao_continua_exibida_sem_ser_regra_de_exclusao_da_negociacao_ativa():
    source = PIPELINE_PAGE.read_text(encoding="utf-8")
    trecho = source.split("const filtrados=", 1)[1].split("const valorTotal=", 1)[0]
    assert trecho.index("if(!item.encerrada)return true") < trecho.index("data_fechamento_prevista")
