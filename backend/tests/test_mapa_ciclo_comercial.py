from datetime import datetime, timezone

from services import mapa_perdas_direcionamento as ciclo


def _qtd(item, padrao=1):
    return int(item.get("quantidade") or padrao)


def _linha(_item):
    return "Direct Drive"


def test_ciclo_novo_sinal_sem_movimento():
    alvo = {"cliente": "CLIENTE A", "responsavel": "MONICA"}
    estado = ciclo._ciclo_cliente(alvo, [], None, [], [])
    assert estado["estado"] == "NOVO_SINAL"
    assert estado["prioridade"] == 0
    assert estado["oportunidades_ativas"] == 0


def test_ciclo_convertido_quando_ha_oportunidade_ganha():
    alvo = {"cliente": "CLIENTE A", "responsavel": "MONICA"}
    hoje = datetime.now(timezone.utc).isoformat()
    estado = ciclo._ciclo_cliente(
        alvo,
        ["c1"],
        "u1",
        [{"cliente_id": "c1", "responsavel_id": "u1", "status": "GANHO", "updated_at": hoje}],
        [],
    )
    assert estado["estado"] == "CONVERTIDO"
    assert estado["ganhos"] == 1


def test_ranking_libera_novo_sinal_antes_de_cliente_convertido(monkeypatch):
    def aplicar(alvos):
        for alvo in alvos:
            if alvo["cliente"] == "CLIENTE CONVERTIDO":
                alvo["ciclo_comercial"] = {"estado": "CONVERTIDO", "rotulo": "Convertido", "prioridade": 4}
            else:
                alvo["ciclo_comercial"] = {"estado": "NOVO_SINAL", "rotulo": "Novo sinal", "prioridade": 0}
        return alvos

    monkeypatch.setattr(ciclo, "_aplicar_ciclo_comercial", aplicar)
    dados = [
        {"cliente": "CLIENTE CONVERTIDO", "responsavel": "MONICA", "quantidade": 50},
        {"cliente": "CLIENTE NOVO", "responsavel": "MONICA", "quantidade": 5},
    ]
    resultado = ciclo.direcionar_registros(dados, _qtd, _linha, limite=1)
    assert resultado["alvos"][0]["cliente"] == "CLIENTE NOVO"
    assert resultado["alvos"][0]["ciclo_comercial"]["estado"] == "NOVO_SINAL"
    assert "CICLO_CRM_DETERMINISTICO" in resultado["regra_ranking"]
