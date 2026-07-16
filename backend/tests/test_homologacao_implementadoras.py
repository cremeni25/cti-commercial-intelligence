import pandas as pd

from core.cti_taxonomy import aliases_implementadora, normalizar_implementadora
from parsers.viena_parser import converter_registro, normalizar_dataframe
from repositories.cti_repository import (
    _adaptar_dominio_para_persistencia,
    _adaptar_persistencia_para_dominio,
)
from services.base_analytics import consolidar_dashboard, consolidar_implementadoras


def test_aliases_homologados_consolidam_nome_oficial():
    assert normalizar_implementadora("IBIPORA") == "IBIPORÃ"
    assert normalizar_implementadora("IBIPORÃ") == "IBIPORÃ"
    assert normalizar_implementadora("PAVAN") == "PAVAN"
    assert normalizar_implementadora("PAVAN INDUSTRIA DE CAMARAS") == "PAVAN"
    assert normalizar_implementadora("PAVAN INDÚSTRIA DE CÂMARAS") == "PAVAN"
    assert normalizar_implementadora("HIGH FLEX") == "HIGH FLEX"
    assert normalizar_implementadora("HIGH FLEX INDUSTRIA") == "HIGH FLEX"
    assert normalizar_implementadora("HIGH FLEX INDÚSTRIA") == "HIGH FLEX"


def test_parser_persistencia_rankings_e_filtros_usam_nome_oficial():
    df = pd.DataFrame([
        [
            "DATA",
            "ESTADO",
            "MUNICIPIO",
            "CHASSI",
            "PLACA",
            "IMPLEMENTADORA",
            "NOME_PROPRIETARIO",
            "VALOR",
        ],
        [45000, "PR", "Ibiporã", "CHASSI1", "AAA1A11", "IBIPORA", "Cliente A", 1000],
        [45001, "SP", "Santos", "CHASSI2", "BBB2B22", "PAVAN INDÚSTRIA DE CÂMARAS", "Cliente B", 2000],
        [45002, "SP", "Campinas", "CHASSI3", "CCC3C33", "HIGH FLEX INDUSTRIA", "Cliente C", 3000],
    ])
    normalizado = normalizar_dataframe(df)
    contexto = {
        "origem_base": "BRASIL",
        "autorizado": None,
        "ano_referencia": None,
        "escopo_operacional": "NACIONAL",
    }

    registros = [
        converter_registro(normalizado, row, "Brasil", contexto, "homologacao.xlsx", indice + 2)
        for indice, row in normalizado.iterrows()
    ]

    assert [r["implementadora"] for r in registros] == ["IBIPORÃ", "PAVAN", "HIGH FLEX"]
    payload = _adaptar_dominio_para_persistencia({"implementadora": "PAVAN INDÚSTRIA DE CÂMARAS"})
    assert payload == {"implementador": "PAVAN"}
    dominio = _adaptar_persistencia_para_dominio({"implementador": "HIGH FLEX INDÚSTRIA"})
    assert dominio["implementadora"] == "HIGH FLEX"

    dashboard = consolidar_dashboard(registros)
    assert dashboard["total_implementadoras"] == 3
    assert {item["nome"] for item in dashboard["ranking_implementadoras"]} == {"IBIPORÃ", "PAVAN", "HIGH FLEX"}

    implementadoras = consolidar_implementadoras(registros)
    pavan = next(item for item in implementadoras if item["nome"] == "PAVAN")
    assert "PAVAN INDÚSTRIA DE CÂMARAS" in pavan["aliases"]
    assert "PAVAN" in aliases_implementadora("PAVAN")
