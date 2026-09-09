from services.mapa_perdas_direcionamento import direcionar_perda_dominante


def _q(item, padrao=1):
    return int(item.get("quantidade") or padrao)


def _linha(item):
    return item.get("linha") or "Não classificado"


def test_direciona_por_responsavel_cliente_e_unidades_sem_duplicar_cliente():
    registros = [
        {"motivo": "Não participamos da proposta", "responsavel": "ANDRÉ", "cliente": "CLIENTE A", "linha": "Direct Drive", "quantidade": 2},
        {"motivo": "Não participamos da proposta", "responsavel": "ANDRÉ", "cliente": "CLIENTE A", "linha": "Direct Drive", "quantidade": 3},
        {"motivo": "Não participamos da proposta", "responsavel": "MÔNICA", "cliente": "CLIENTE B", "linha": "Trailer", "quantidade": 4},
        {"motivo": "Preço Carrier mais alto", "responsavel": "ANDRÉ", "cliente": "CLIENTE C", "linha": "Trailer", "quantidade": 9},
    ]
    resultado = direcionar_perda_dominante(registros, "Não participamos da proposta", _q, _linha)
    assert len(resultado["alvos"]) == 2
    assert resultado["alvos"][0]["cliente"] == "CLIENTE A"
    assert resultado["alvos"][0]["unidades"] == 5
    assert resultado["alvos"][0]["ocorrencias"] == 2
    assert "ANDRÉ → CLIENTE A (5 un.; Direct Drive)" in resultado["texto"]
    assert "MÔNICA → CLIENTE B (4 un.; Trailer)" in resultado["texto"]
