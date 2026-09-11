from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = (ROOT / "routers" / "crm_atividades_governanca_router.py").read_text(encoding="utf-8")


def test_atividade_reutiliza_negociacao_aberta_do_cliente():
    assert "_oportunidades_abertas_cliente" in ROUTER
    assert "if len(abertas) == 1" in ROUTER
    assert "return str(abertas[0].get(\"id\")" in ROUTER


def test_multiplas_negociacoes_exigem_selecao_explicita():
    assert "Este cliente possui mais de uma negociação aberta" in ROUTER


def test_atividade_e_conclusao_registram_evento_no_historico_da_negociacao():
    assert "_registrar_evento_negociacao" in ROUTER
    assert '"Nova atualização registrada no processo comercial."' in ROUTER
    assert '"Atualização do processo comercial concluída."' in ROUTER


def test_encerramento_possui_motivos_formais_e_preserva_historico():
    for motivo in (
        "VENDA_CONCLUIDA",
        "PERDA_CONCORRENCIA",
        "DESISTENCIA_CLIENTE",
        "SEM_CONTINUIDADE",
        "OUTRO",
    ):
        assert motivo in ROUTER
    assert '@router.put("/oportunidades/{oportunidade_id}/encerrar")' in ROUTER
    assert '"Processo comercial encerrado e preservado no histórico do cliente."' in ROUTER


def test_encerramento_remove_pendencias_da_operacao_sem_apagar_historico():
    assert '"status": "CANCELADA"' in ROUTER
    assert 'supabase.table("cti_oportunidade_historico")' in ROUTER
    assert ".delete(" not in ROUTER
