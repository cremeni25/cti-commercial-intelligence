from __future__ import annotations

import pytest

from services import ia_comercial_sintese_crm as multifonte
from services.ia_comercial_cti import IAComercialOpenAIError


def test_multifonte_universal_aceita_consulta_e_catalogo_cti():
    metadados = {
        "ferramentas": [
            {"tipo": "CTI", "ferramenta": "catalogar_universo_cti", "argumentos": {}},
            {
                "tipo": "CTI",
                "ferramenta": "consultar_universo_cti",
                "argumentos": {"fonte": "implementadoras_cadastro"},
            },
        ]
    }

    multifonte._auditar_ferramentas_multifonte(
        metadados,
        {"universo_cti", "web"},
    )


def test_multifonte_universal_rejeita_ferramenta_cti_fora_da_interface_universal():
    metadados = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_dominio_cti",
                "argumentos": {"dominio": "clientes"},
            }
        ]
    }

    with pytest.raises(IAComercialOpenAIError) as exc:
        multifonte._auditar_ferramentas_multifonte(
            metadados,
            {"universo_cti", "web"},
        )

    assert exc.value.codigo == "AGENT_MULTISOURCE_SCOPE_VIOLATION"


def test_multifonte_legado_continua_delegado_para_auditoria_historica():
    metadados = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_dominio_cti",
                "argumentos": {"dominio": "clientes"},
            }
        ]
    }

    with pytest.raises(IAComercialOpenAIError):
        multifonte._auditar_ferramentas_multifonte(
            metadados,
            {"web", "produtos", "vendas"},
        )
