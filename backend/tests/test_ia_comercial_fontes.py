from services.ia_comercial_agente_homologacao import _fontes_web


def test_fontes_web_vazias_sem_saida():
    class Resposta:
        output = []

    assert _fontes_web(Resposta()) == []
