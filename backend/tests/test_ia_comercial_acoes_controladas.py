from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routers import ia_comercial_acoes_router as acoes


def usuario_admin():
    return SimpleNamespace(id="user-1", tipo_usuario="ADMIN_MASTER", nome="Teste")


def escopo_base():
    return {
        "clientes": [{"id": "cli-1", "nome": "ABC CARGAS LTDA"}],
        "oportunidades": [{"id": "opp-1", "cliente_id": "cli-1", "titulo": "Venda X4"}],
        "pedidos": [
            {
                "id": "ped-1",
                "numero": "PED-20260804-A24FA6A7",
                "cliente_id": "cli-1",
                "status_ciclo": "CARRIER",
            }
        ],
        "atividades": [
            {
                "id": "atv-1",
                "cliente_id": "cli-1",
                "usuario_id": "user-1",
                "titulo": "Acompanhamento do pedido PED-20260804-A24FA6A7",
            }
        ],
    }


def test_criar_atividade_forca_usuario_autenticado_e_exibe_razao_social(monkeypatch):
    monkeypatch.setattr(acoes, "_escopo_autorizado", lambda *_: escopo_base())
    payload, resumo = acoes._normalizar_payload(
        "CRIAR_ATIVIDADE_CRM",
        {
            "cliente_id": "cli-1",
            "oportunidade_id": "opp-1",
            "pedido_id": "ped-1",
            "usuario_id": "outro-usuario",
            "tipo": "visita",
            "titulo": "Visita de acompanhamento",
        },
        usuario_admin(),
    )
    assert payload["usuario_id"] == "user-1"
    assert payload["status"] == "PENDENTE"
    assert payload["tipo"] == "VISITA"
    assert "ABC CARGAS LTDA" in resumo
    assert "PED-20260804-A24FA6A7" in resumo
    assert "cli-1" not in resumo
    assert "ped-1" not in resumo


def test_acao_recusa_alvo_fora_do_escopo(monkeypatch):
    monkeypatch.setattr(acoes, "_escopo_autorizado", lambda *_: escopo_base())
    with pytest.raises(HTTPException) as exc:
        acoes._normalizar_payload(
            "CRIAR_ATIVIDADE_CRM",
            {"cliente_id": "cli-nao-autorizado", "tipo": "VISITA"},
            usuario_admin(),
        )
    assert exc.value.status_code == 403


def test_ia_nao_pode_confirmar_carrier_manualmente(monkeypatch):
    monkeypatch.setattr(acoes, "_escopo_autorizado", lambda *_: escopo_base())
    with pytest.raises(HTTPException) as exc:
        acoes._normalizar_payload(
            "ATUALIZAR_CICLO_PEDIDO",
            {"pedido_id": "ped-1", "etapa": "CARRIER"},
            usuario_admin(),
        )
    assert exc.value.status_code == 422
    assert "não pode confirmar CARRIER" in exc.value.detail


def test_ciclo_permite_apenas_etapas_posteriores_e_exibe_numero_pedido(monkeypatch):
    monkeypatch.setattr(acoes, "_escopo_autorizado", lambda *_: escopo_base())
    payload, resumo = acoes._normalizar_payload(
        "ATUALIZAR_CICLO_PEDIDO",
        {
            "pedido_id": "ped-1",
            "etapa": "FATURADO",
            "numero_nf": "NF-10",
            "numero_serie_nf": "SERIE-10",
        },
        usuario_admin(),
    )
    assert payload["etapa"] == "FATURADO"
    assert payload["numero_nf"] == "NF-10"
    assert payload["numero_serie_nf"] == "SERIE-10"
    assert "PED-20260804-A24FA6A7" in resumo
    assert "ABC CARGAS LTDA" in resumo
    assert "ped-1" not in resumo


def test_status_atividade_exibe_titulo_e_cliente_sem_uuid(monkeypatch):
    monkeypatch.setattr(acoes, "_escopo_autorizado", lambda *_: escopo_base())
    payload, resumo = acoes._normalizar_payload(
        "ATUALIZAR_STATUS_ATIVIDADE",
        {"atividade_id": "atv-1", "status": "CONCLUIDA"},
        usuario_admin(),
    )
    assert payload == {"atividade_id": "atv-1", "status": "CONCLUIDA"}
    assert "Acompanhamento do pedido PED-20260804-A24FA6A7" in resumo
    assert "ABC CARGAS LTDA" in resumo
    assert "atv-1" not in resumo


def test_resultado_publico_remove_identificadores_tecnicos():
    publico = acoes._resultado_publico(
        {
            "tipo_acao": "CRIAR_ATIVIDADE_CRM",
            "registro": {
                "id": "uuid-registro",
                "cliente_id": "uuid-cliente",
                "pedido_id": "uuid-pedido",
                "usuario_id": "uuid-usuario",
                "tipo": "ACOMPANHAMENTO",
                "titulo": "Acompanhamento do pedido PED-20260804-A24FA6A7",
                "status": "PENDENTE",
            },
        }
    )
    assert publico is not None
    assert publico["registro"] == {
        "tipo": "ACOMPANHAMENTO",
        "titulo": "Acompanhamento do pedido PED-20260804-A24FA6A7",
        "status": "PENDENTE",
    }


def test_confirmacao_repetida_e_idempotente_sem_expor_id_do_registro(monkeypatch):
    monkeypatch.setattr(
        acoes,
        "_carregar_proposta",
        lambda *_: {
            "id": "acao-1",
            "detalhes": {
                "status": "EXECUTADA",
                "resumo": "Criar atividade ACOMPANHAMENTO para o cliente ABC CARGAS LTDA.",
                "resultado": {
                    "tipo_acao": "CRIAR_ATIVIDADE_CRM",
                    "registro": {"id": "atv-9", "cliente_id": "cli-1", "tipo": "ACOMPANHAMENTO"},
                },
            },
        },
    )
    chamado = {"executar": 0}

    def nunca_executar(*_args, **_kwargs):
        chamado["executar"] += 1
        raise AssertionError("ação não deve ser executada novamente")

    monkeypatch.setattr(acoes, "_executar", nunca_executar)
    resultado = acoes.confirmar_acao(
        "acao-1",
        acoes.ConfirmarAcaoRequest(confirmar=True),
        usuario_admin(),
    )
    assert resultado["status"] == "EXECUTADA"
    assert resultado["idempotencia"] == "JA_EXECUTADA_SEM_REPETICAO"
    assert resultado["resumo"].endswith("ABC CARGAS LTDA.")
    assert resultado["resultado"]["registro"] == {"tipo": "ACOMPANHAMENTO"}
    assert chamado["executar"] == 0


def test_status_atividade_restrito(monkeypatch):
    monkeypatch.setattr(acoes, "_escopo_autorizado", lambda *_: escopo_base())
    with pytest.raises(HTTPException) as exc:
        acoes._normalizar_payload(
            "ATUALIZAR_STATUS_ATIVIDADE",
            {"atividade_id": "atv-1", "status": "EXCLUIDA"},
            usuario_admin(),
        )
    assert exc.value.status_code == 422


def test_confirmacao_concorrente_sem_reserva_nao_executa(monkeypatch):
    proposta_pendente = {
        "id": "acao-1",
        "detalhes": {
            "status": "PENDENTE_CONFIRMACAO",
            "tipo_acao": "CRIAR_ATIVIDADE_CRM",
            "payload": {"cliente_id": "cli-1", "tipo": "ACOMPANHAMENTO"},
            "resumo": "Criar atividade ACOMPANHAMENTO para o cliente ABC CARGAS LTDA.",
        },
    }
    proposta_em_execucao = {
        "id": "acao-1",
        "detalhes": {
            **proposta_pendente["detalhes"],
            "status": "EM_EXECUCAO",
        },
    }
    leituras = iter([proposta_pendente, proposta_em_execucao])
    monkeypatch.setattr(acoes, "_carregar_proposta", lambda *_: next(leituras))
    monkeypatch.setattr(acoes, "_escopo_autorizado", lambda *_: escopo_base())
    monkeypatch.setattr(acoes, "_reservar_execucao", lambda *_: False)
    chamado = {"executar": 0}

    def nunca_executar(*_args, **_kwargs):
        chamado["executar"] += 1
        raise AssertionError("requisição que perdeu a reserva não pode executar")

    monkeypatch.setattr(acoes, "_executar", nunca_executar)
    with pytest.raises(HTTPException) as exc:
        acoes.confirmar_acao(
            "acao-1",
            acoes.ConfirmarAcaoRequest(confirmar=True),
            usuario_admin(),
        )
    assert exc.value.status_code == 409
    assert "já está em execução" in exc.value.detail
    assert chamado["executar"] == 0


def test_cancelamento_recusa_acao_em_execucao(monkeypatch):
    monkeypatch.setattr(
        acoes,
        "_carregar_proposta",
        lambda *_: {
            "id": "acao-1",
            "detalhes": {
                "status": "EM_EXECUCAO",
                "tipo_acao": "CRIAR_ATIVIDADE_CRM",
                "resumo": "Criar atividade ACOMPANHAMENTO para o cliente ABC CARGAS LTDA.",
            },
        },
    )
    with pytest.raises(HTTPException) as exc:
        acoes.cancelar_acao("acao-1", usuario_admin())
    assert exc.value.status_code == 409
    assert "em execução" in exc.value.detail
