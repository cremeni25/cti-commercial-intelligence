from routers import modulos_router


REGISTROS = [
    {
        "origem_base": "BRASIL",
        "estado": "BA",
        "ddd": "071",
        "implementadora": "Implementadora Bahia",
        "cliente": "Cliente BA",
        "cidade": "Salvador",
        "linha": "SUPRA",
        "valor": 1000,
    },
    {
        "origem_base": "VIENA_SP",
        "autorizado": "VIENA",
        "estado": "SP",
        "ddd": "011",
        "implementadora": "Implementadora Viena",
        "cliente": "Cliente SP",
        "cidade": "São Paulo",
        "linha": "XARIOS",
        "valor": 2000,
    },
]


def test_listar_implementadoras_respeita_contexto(monkeypatch):
    monkeypatch.setattr(modulos_router.repository, "buscar_cti_anfir", lambda: REGISTROS)

    brasil = modulos_router.listar_implementadoras(contexto="brasil")
    viena = modulos_router.listar_implementadoras(contexto="viena-sp")
    bahia = modulos_router.listar_implementadoras(contexto="uf-ba")

    assert {item["nome"] for item in brasil} == {"BAHIA IMPLEMENTADORA", "IMPLEMENTADORA VIENA"}
    assert [item["nome"] for item in viena] == ["IMPLEMENTADORA VIENA"]
    assert [item["nome"] for item in bahia] == ["BAHIA IMPLEMENTADORA"]
    assert bahia[0]["valor_total"] == 1000
