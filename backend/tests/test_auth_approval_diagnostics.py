from datetime import UTC, datetime

from routers.auth_router import _agora_iso


def test_agora_iso_retorna_timestamp_utc_valido():
    valor = _agora_iso()
    instante = datetime.fromisoformat(valor)

    assert instante.tzinfo is not None
    assert instante.utcoffset() == UTC.utcoffset(instante)
