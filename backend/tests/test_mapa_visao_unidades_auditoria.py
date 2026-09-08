from pathlib import Path

from routers import crm_scope_mapa_equipe_router as mapa

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "crm_scope_mapa_equipe_router.py"


def test_familias_somam_unidades_e_nao_linhas(monkeypatch):
    monkeypatch.setattr(mapa, "classificar_linha", lambda item: item["linha"])
    registros = [
        {"linha": "TR", "quantidade": 3},
        {"linha": "TR", "quantidade": 2},
        {"linha": "DT", "quantidade": 4},
        {"linha": "DD", "quantidade": 1},
    ]
    assert mapa._familias(registros) == {"trailer": 5, "diesel_truck": 4, "direct_drive": 1}


def test_unidades_separam_quantidade_de_numero_de_registros():
    registros = [{"quantidade": 4}, {"quantidade": 2}, {"quantidade": 1}]
    assert len(registros) == 3
    assert mapa._unidades(registros) == 7


def test_visao_geral_nao_usa_len_para_total_de_mercado():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "total_viena = _unidades(mercado_total, 1)" in fonte
    assert "total_regiao = _unidades(anf, 1)" in fonte
    assert "unidades_individuais = _unidades(anf_individual, 1)" in fonte
    assert '"mercado": unidades_individuais' in fonte


def test_drilldown_anfir_expõe_ocorrencias_e_unidades_separadamente():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "total_unidades = _unidades(registros, 1) if camada == \"anfir\" else None" in fonte
    assert '"total_unidades": total_unidades' in fonte
    assert "total_registros=ocorrencias; total_unidades=soma_quantidade" in fonte


def test_metadado_nao_declara_carteira_atual_como_autoria_anfir():
    fonte = ROUTER.read_text(encoding="utf-8")
    assert "ANFIR=AUTORIA_DA_FONTE" in fonte
    assert "DDD_NAO_ATRIBUI_RESPONSAVEL" in fonte
