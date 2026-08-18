from services.ia_comercial_auditoria_proveniencia import construir_auditoria_evidencial


def _metadados_base(*, com_web: bool = False):
    fontes = [
        {"tipo": "CTI", "descricao": "Ferramentas internas autorizadas do CTI."},
        {
            "tipo": "ANEXO_TEMPORARIO",
            "descricao": "Pulsor eCool.pdf · SHA-256 870fbf98d3fa…",
        },
    ]
    if com_web:
        fontes.append(
            {
                "tipo": "WEB",
                "descricao": "Carrier Transicold",
                "url": "https://www.carrier.com/truck-trailer/en/worldwide/",
            }
        )

    return {
        "fontes": fontes,
        "anexos": [
            {
                "nome": "Pulsor eCool.pdf",
                "tipo": "PDF",
                "sha256": "870fbf98d3fad745dc450510ff527ee1361738b148f216cfb9e3c341e6c7ea37",
                "estrutura": {"paginas": 1, "paginas_com_texto": 1},
                "mime_type": "application/pdf",
                "temporario": True,
                "publicado_cti": False,
                "tamanho_bytes": 311915,
            }
        ],
        "ferramentas": [
            {
                "tipo": "CTI",
                "ferramenta": "consultar_universo_cti",
                "argumentos": {
                    "fonte": "clientes",
                    "filtros": [
                        {"campo": "nome", "valor": "RD", "valores": [], "operador": "contains"}
                    ],
                },
                "resumo": {"erro": None, "total_retornado": 11},
            }
        ],
        "evidencias_requeridas": ["universo_cti"],
        "evidencias_atendidas": ["universo_cti"],
        "controle_temporal_pergunta": "sem_periodo_explicito_todo_historico",
        "controle_recorte_base": "restricoes_explicitas_pergunta",
        "web_requerida": com_web,
        "web_fontes_validas": 1 if com_web else 0,
        "web_urls_auditaveis": ["https://www.carrier.com/truck-trailer/en/worldwide/"] if com_web else [],
        "somente_leitura": True,
        "controle_anexos": "temporarios_nao_publicados_nao_operacionais",
    }


def _por_texto(auditoria, trecho):
    for item in auditoria["afirmacoes"]:
        if trecho.casefold() in item["texto"].casefold():
            return item
    raise AssertionError(f"Afirmação não encontrada: {trecho}")


def test_ia010_separa_anexo_cti_controle_e_inferencia_sem_web():
    resposta = """
A seguir está a análise do anexo Pulsor eCool.pdf e como pode ser utilizado no CTI.

## 1) O que o arquivo contém (extraído do próprio PDF)
Trata-se de uma proposta comercial emitida para RD SAUDE.
**CNPJ:** 61.585.865/0001-51
**Quantidade:** 27 unidades
**Modelo:** Pulsor 6 eCool

## 2) Fatos internos CTI (evidência desta execução)
Foram encontrados 11 clientes no CRM cujo nome contém RD.
Dentro desses registros, não apareceu um cliente com nome exatamente RD SAUDE.

## 3) Fatos externos verificados (web)
Nenhuma consulta web foi realizada nesta execução.

## 4) Como essas informações podem ser utilizadas no CTI (inferências/recomendações operacionais)
Usar os dados do PDF para localizar o cliente no CRM e evitar duplicidade de conta.
Criar ou planejar atividade de acompanhamento da proposta.
"""

    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados_base(com_web=False),
        pergunta_atual="Analise este arquivo e me diga como pode ser utilizado no CTI.",
    )
    auditoria = resultado["auditoria_evidencial"]

    origens = {item["id"]: item for item in auditoria["origens_execucao"]}
    assert origens["ANEXO_1"]["tipo"] == "ANEXO_TEMPORARIO"
    assert origens["ANEXO_1"]["sha256"].startswith("870fbf98")
    assert origens["ANEXO_1"]["estrutura"]["paginas"] == 1
    assert origens["ANEXO_1"]["temporario"] is True
    assert origens["ANEXO_1"]["publicado_cti"] is False

    fato_anexo = _por_texto(auditoria, "RD SAUDE")
    assert fato_anexo["tipo"] == "FATO_ANEXO"
    assert fato_anexo["fontes_evidencia"] == ["ANEXO_1"]
    assert fato_anexo["status_rastreabilidade"] == "RASTREAVEL"

    fato_cti = _por_texto(auditoria, "11 clientes")
    assert fato_cti["tipo"] == "FATO_CTI"
    assert fato_cti["fontes_evidencia"] == ["CTI_1"]
    assert fato_cti["status_rastreabilidade"] == "RASTREAVEL"

    fato_controle = _por_texto(auditoria, "Nenhuma consulta web")
    assert fato_controle["tipo"] == "FATO_CONTROLE"
    assert fato_controle["fontes_evidencia"] == ["EXECUCAO_1"]
    assert fato_controle["status_rastreabilidade"] == "RASTREAVEL"

    recomendacao = _por_texto(auditoria, "evitar duplicidade")
    assert recomendacao["tipo"] == "INFERENCIA_RECOMENDACAO"
    assert "ANEXO_1" in recomendacao["derivada_de"]
    assert "CTI_1" in recomendacao["derivada_de"]
    assert recomendacao["status_rastreabilidade"] == "RASTREAVEL"

    assert not any(item["tipo"] == "FATO_WEB" for item in auditoria["afirmacoes"])
    assert auditoria["totais"]["afirmacoes_sem_evidencia_explicita"] == 0
    assert resultado["controle_proveniencia_evidencia"] == "ia010_anexo_cti_web_inferencia_explicitos"


def test_ia010_fato_web_exige_fonte_web_real():
    resposta = """
## 1) O que o arquivo contém (extraído do próprio PDF)
O documento cita o modelo Pulsor 6 eCool.

## 2) Fatos internos CTI
O CRM contém clientes relacionados ao termo consultado.

## 3) Fatos externos verificados (web)
A Carrier mantém presença pública para soluções de refrigeração de transporte.
"""

    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados_base(com_web=True),
        pergunta_atual="Cruze o anexo com CTI e web.",
    )
    auditoria = resultado["auditoria_evidencial"]
    fato_web = _por_texto(auditoria, "presença pública")

    assert fato_web["tipo"] == "FATO_WEB"
    assert fato_web["fontes_evidencia"]
    assert all(fonte.startswith("WEB_") for fonte in fato_web["fontes_evidencia"])
    assert fato_web["status_rastreabilidade"] == "RASTREAVEL"
