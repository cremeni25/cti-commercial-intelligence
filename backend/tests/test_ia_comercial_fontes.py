from services.ia_comercial_cti import _fontes_web


def test_fontes_web_vazias_sem_anotacoes():
    class Mensagem:
        annotations = []

    assert _fontes_web(Mensagem()) == []
