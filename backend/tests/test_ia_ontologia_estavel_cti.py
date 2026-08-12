from __future__ import annotations

from services import ia_comercial_agente_crm as crm
from services import ia_comercial_guard_semantico as guard
from services import ia_comercial_ontologia as ontologia


PERGUNTA_REAL = (
    "entre os dados contidos no cti e através de pesquisa na web, "
    "relacione as 05 maiores implementadoras do Brasil"
)


def test_pergunta_real_exige_catalogo_universo_e_web():
    assert crm._fontes_requeridas_universais(PERGUNTA_REAL) == {
        "catalogo_cti",
        "universo_cti",
        "web",
    }


def test_ontologia_implementadora_preserva_setor_de_transporte():
    entidade = ontologia.ONTOLOGIA_COMERCIAL_CTI["entidades"]["implementadora"]
    texto = " ".join(
        [
            entidade["definicao"],
            entidade["contexto_web_obrigatorio"],
            *entidade["nao_e"],
        ]
    ).casefold()

    assert "implementos" in texto
    assert "transporte" in texto
    assert "sap" in texto
    assert "oracle" in texto
    assert entidade["fonte_analitica_historica"] == "historico_anfir"
    assert entidade["campo_historico"] == "implementadora"


def test_cadastro_implementadoras_nao_pode_ser_usado_para_ranking_por_count():
    erro = ontologia._consulta_analiticamente_incompativel(
        "implementadoras_cadastro",
        agrupar_por=["nome"],
        metricas=[{"operacao": "count", "campo": None, "alias": "registros"}],
        ordenar_por="registros",
    )

    assert erro is not None
    assert erro["codigo"] == "FONTE_FINALIDADE_ANALITICA_INCOMPATIVEL"
    assert erro["fonte_analitica_sugerida"] == "historico_anfir"


def test_cadastro_implementadoras_continua_valido_para_listagem_sem_agregacao():
    erro = ontologia._consulta_analiticamente_incompativel(
        "implementadoras_cadastro",
        agrupar_por=[],
        metricas=[],
        ordenar_por="nome",
    )

    assert erro is None


def test_historico_anfir_permanece_fonte_analitica_para_ranking():
    erro = ontologia._consulta_analiticamente_incompativel(
        "historico_anfir",
        agrupar_por=["implementadora"],
        metricas=[{"operacao": "count", "campo": None, "alias": "total_registros"}],
        ordenar_por="total_registros",
    )

    assert erro is None


def test_instrucoes_barram_deriva_para_implementadoras_de_software():
    instrucoes = crm._INSTRUCOES_UNIVERSAIS.casefold()

    assert "ontologia comercial cti" in instrucoes
    assert "sap" in instrucoes
    assert "oracle" in instrucoes
    assert "servicenow" in instrucoes
    assert "semanticamente inválidos" in instrucoes
    assert "mesma pergunta" in instrucoes
    assert "mesma classe semântica" in instrucoes


def test_instrucao_de_evidencia_exige_catalogo_antes_da_fonte_e_web():
    instrucao = crm._instrucao_evidencias_faltantes_universal(
        {"catalogo_cti", "universo_cti", "web"}
    ).casefold()

    assert "catalogar_universo_cti antes" in instrucao
    assert "ontologia" in instrucao
    assert "finalidade" in instrucao


def test_guard_detecta_ranking_cadastral_sem_historico():
    metadados = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "argumentos": {
                    "fonte": "implementadoras_cadastro",
                    "agrupar_por": [],
                    "metricas": [],
                },
            }
        ],
        "fontes": [],
    }

    assert "ranking_de_implementadora_sem_fonte_historica" in guard._motivos_deriva(
        PERGUNTA_REAL,
        metadados,
    )


def test_guard_detecta_web_de_sap_e_aceita_web_de_implementos_rodoviarios():
    base_meta = {
        "ferramentas": [
            {
                "tipo": "CTI",
                "argumentos": {
                    "fonte": "historico_anfir",
                    "agrupar_por": ["implementadora"],
                    "metricas": [{"operacao": "count", "campo": None, "alias": "total"}],
                },
            }
        ]
    }

    meta_sap = {
        **base_meta,
        "fontes": [
            {"url": "https://exemplo.com/sap", "descricao": "Implementadora de ERP SAP e Oracle"}
        ],
    }
    assert "web_fora_da_ontologia_de_implementadora" in guard._motivos_deriva(
        PERGUNTA_REAL,
        meta_sap,
    )

    meta_rodoviario = {
        **base_meta,
        "fontes": [
            {
                "url": "https://exemplo.com/implementos",
                "descricao": "Fabricantes de implementos rodoviários, carrocerias e semirreboques",
            }
        ],
    }
    assert guard._motivos_deriva(PERGUNTA_REAL, meta_rodoviario) == []
