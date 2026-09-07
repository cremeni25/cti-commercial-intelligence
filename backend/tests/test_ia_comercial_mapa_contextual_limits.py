import pytest
from pydantic import ValidationError

from routers.ia_comercial_mapa_router import PerguntaContextual, TurnoContextual


def test_historico_contextual_aceita_ate_oito_turnos():
    payload = PerguntaContextual(
        pergunta="continue",
        historico=[TurnoContextual(role="user", content=f"turno {i}") for i in range(8)],
    )
    assert len(payload.historico) == 8


def test_historico_contextual_rejeita_mais_de_oito_turnos():
    with pytest.raises(ValidationError):
        PerguntaContextual(
            pergunta="continue",
            historico=[TurnoContextual(role="user", content=f"turno {i}") for i in range(9)],
        )
