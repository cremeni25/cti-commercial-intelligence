from core.ia_agente_homologacao_config import carregar_ia_agente_homologacao_config


def test_agente_desligado_por_padrao(monkeypatch):
    monkeypatch.delenv("CTI_IA_AGENTE_HOMOLOGACAO", raising=False)
    monkeypatch.delenv("CTI_IA_AGENTE_SOMENTE_LEITURA", raising=False)
    monkeypatch.delenv("CTI_AMBIENTE", raising=False)

    config = carregar_ia_agente_homologacao_config()

    assert config.habilitada is False
    assert config.somente_leitura is True
    assert config.ambiente == "production"
    assert config.pronta_para_homologacao is False


def test_agente_nao_fica_pronto_em_producao(monkeypatch):
    monkeypatch.setenv("CTI_IA_AGENTE_HOMOLOGACAO", "true")
    monkeypatch.setenv("CTI_IA_AGENTE_SOMENTE_LEITURA", "true")
    monkeypatch.setenv("CTI_AMBIENTE", "production")

    config = carregar_ia_agente_homologacao_config()

    assert config.habilitada is True
    assert config.pronta_para_homologacao is False


def test_agente_nao_fica_pronto_com_escrita(monkeypatch):
    monkeypatch.setenv("CTI_IA_AGENTE_HOMOLOGACAO", "true")
    monkeypatch.setenv("CTI_IA_AGENTE_SOMENTE_LEITURA", "false")
    monkeypatch.setenv("CTI_AMBIENTE", "homologation")

    config = carregar_ia_agente_homologacao_config()

    assert config.somente_leitura is False
    assert config.pronta_para_homologacao is False


def test_agente_pronto_somente_em_homologacao_e_leitura(monkeypatch):
    monkeypatch.setenv("CTI_IA_AGENTE_HOMOLOGACAO", "true")
    monkeypatch.setenv("CTI_IA_AGENTE_SOMENTE_LEITURA", "true")
    monkeypatch.setenv("CTI_AMBIENTE", "homologation")

    config = carregar_ia_agente_homologacao_config()

    assert config.pronta_para_homologacao is True
