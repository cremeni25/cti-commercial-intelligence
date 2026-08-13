from services import ia_comercial_artefatos_patch as patch


def test_relatorio_crm_ignora_historico_anterior(monkeypatch):
    capturado = {}

    def falso_gerador(*, mensagem, historico, usuario_id, tipo_usuario):
        capturado["historico"] = historico
        return "relatorio novo", {"fontes": [{"tipo": "CTI"}]}

    monkeypatch.setattr(patch, "_ORIGINAL_GERAR_RESPOSTA", falso_gerador)
    historico = [
        {"role": "user", "content": "pesquisa anterior"},
        {"role": "assistant", "content": "números antigos que não podem ser reutilizados"},
    ]

    resposta, metadados = patch.gerar_resposta_agente(
        mensagem="RELATÓRIO CRM — PIPELINE EXECUTIVO. Gere relatório em PDF.",
        historico=historico,
        usuario_id="usuario-teste",
        tipo_usuario="ADMIN_MASTER",
    )

    assert resposta == "relatorio novo"
    assert capturado["historico"] == []
    assert metadados["controle_relatorio_crm"] == "execucao_tematica_isolada_sem_historico"
    assert metadados["historico_relatorio_reutilizado"] is False
    assert metadados["snapshot_relatorio_origem"] == "execucao_atual"


def test_pergunta_comum_preserva_historico(monkeypatch):
    capturado = {}

    def falso_gerador(*, mensagem, historico, usuario_id, tipo_usuario):
        capturado["historico"] = historico
        return "resposta", {}

    monkeypatch.setattr(patch, "_ORIGINAL_GERAR_RESPOSTA", falso_gerador)
    historico = [{"role": "assistant", "content": "contexto válido da conversa"}]

    patch.gerar_resposta_agente(
        mensagem="Qual é a próxima ação deste cliente?",
        historico=historico,
        usuario_id="usuario-teste",
        tipo_usuario="ADMIN_MASTER",
    )

    assert capturado["historico"] == historico
