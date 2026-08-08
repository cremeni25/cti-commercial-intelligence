from services.ia_comercial_cti import _fontes_responses


def test_fontes_web_vazias_sem_saida():
    class Resposta:
        output = []

    assert _fontes_responses(Resposta()) == []
