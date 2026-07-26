import pytest

from services.product_catalog_service import (
    normalizar_alias,
    validar_alias,
    listar_catalogo,
)


def test_normaliza_alias_sem_confundir_formatacao():
    assert normalizar_alias("  CM-500-AE ") == "CM 500 AE"
    assert normalizar_alias("Direct-Drive") == "DIRECT DRIVE"


@pytest.mark.parametrize("termo", ["caminhão", "truck", "van", "furgão", "VUC", "carreta", "semirreboque"])
def test_bloqueia_termos_genericos_de_veiculo(termo):
    with pytest.raises(ValueError):
        validar_alias(termo)


def test_catalogo_fallback_preserva_taxonomia_homologada(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    from services import product_catalog_service as service
    service._client.cache_clear()

    catalogo = listar_catalogo()

    assert catalogo["source"] == "fallback"
    assert catalogo["editable"] is False
    linhas = {linha["code"]: linha for linha in catalogo["lines"]}
    assert set(linhas) == {"TR", "DT", "DD"}
    assert any(modelo["canonical_name"] == "X4-7500" for modelo in linhas["TR"]["models"])
    assert any(modelo["canonical_name"] == "SUPRA 1150" for modelo in linhas["DT"]["models"])
    assert any(modelo["canonical_name"] == "CM500AE" for modelo in linhas["DD"]["models"])
