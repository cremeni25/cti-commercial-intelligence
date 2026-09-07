from types import SimpleNamespace

from routers import ia_comercial_mapa_router as router


def _usuario():
    return SimpleNamespace(id="master-1", tipo_usuario="MASTER")


def _visao():
    return {
        "selecao": {"modo": "RESPONSAVEL", "id": "resp-1", "nome": "Mônica", "codigo_regional": "011-L", "ddds": ["011"]},
        "equipe": [{"id": "resp-1", "tipo_usuario": "VENDEDOR", "nome": "Mônica"}],
        "mercado": {
            "mercado_real_viena_2026": 100,
            "mercado_real_selecao_2026": 20,
            "participacao_regiao_no_mercado_real_pct": 20,
            "familias": {"trailer": 8, "diesel_truck": 7, "direct_drive": 5},
            "clientes_unicos": 15,
        },
        "evidencias": {
            "historico_registros_2026": 10,
            "historico_unidades_2026": 12,
            "motivos_perda_historico": [],
            "crm_registros": 3,
            "crm_ativos": 2,
            "crm_valor_ativo": 250000,
            "crm_status": [{"nome": "ABERTA", "quantidade": 2}],
        },
        "reconciliacao": {"clientes_anfir": 15, "clientes_historico": 8, "clientes_crm": 3, "nas_tres_fontes": 2},
    }


def test_pergunta_contextual_reaplica_selecao_e_encaminha_historico(monkeypatch):
    visao = _visao()
    chamadas = {}

    def fake_visao_equipe(responsavel_id=None, usuario=None):
        chamadas["responsavel_id"] = responsavel_id
        chamadas["usuario"] = usuario
        return visao

    def fake_agente(mensagem, historico, usuario_id, tipo_usuario):
        chamadas["mensagem"] = mensagem
        chamadas["historico"] = historico
        chamadas["usuario_id"] = usuario_id
        chamadas["tipo_usuario"] = tipo_usuario
        return "Resposta contextual", {"fontes": [{"tipo": "CTI"}]}

    monkeypatch.setattr(router, "visao_equipe", fake_visao_equipe)
    monkeypatch.setattr(router, "gerar_resposta_agente", fake_agente)

    payload = router.PerguntaContextual(
        pergunta="Onde devo concentrar atenção?",
        historico=[
            router.TurnoContextual(role="user", content="E as perdas?"),
            router.TurnoContextual(role="assistant", content="Há concentração em um motivo."),
        ],
    )
    resposta = router.inteligencia_comercial_contextual(payload, responsavel_id="resp-1", usuario=_usuario())

    assert chamadas["responsavel_id"] == "resp-1"
    assert chamadas["usuario_id"] == "resp-1"
    assert chamadas["tipo_usuario"] == "VENDEDOR"
    assert chamadas["historico"] == [
        {"role": "user", "content": "E as perdas?"},
        {"role": "assistant", "content": "Há concentração em um motivo."},
    ]
    assert "Onde devo concentrar atenção?" in chamadas["mensagem"]
    assert "SNAPSHOT ATUAL DA SELEÇÃO" in chamadas["mensagem"]
    assert resposta["analise"] == "Resposta contextual"
    assert resposta["somente_leitura"] is True
    assert resposta["persistido"] is False
