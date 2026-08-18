from services.ia_comercial_ia010_continuidade import (
    _TEM_ANEXO,
    _USAR_CTI,
    _ferramentas_ia010,
    _fontes_requeridas_ia010,
)
from services.ia_comercial_auditoria_proveniencia import construir_auditoria_evidencial


PERGUNTA_REAL = (
    "Compare as capacidades e busque em frigoking e thermoking quais as equivalências "
    "em capacidade e operação"
)


def test_anexo_com_busca_externa_nao_reintroduz_cti_e_exige_web():
    token = _TEM_ANEXO.set(True)
    try:
        assert _fontes_requeridas_ia010(PERGUNTA_REAL) == {"web"}
    finally:
        _TEM_ANEXO.reset(token)


def test_busque_externo_exige_web_mesmo_sem_palavra_web():
    assert _fontes_requeridas_ia010("Busque nos fabricantes concorrentes as capacidades atuais") == {"web"}


def test_sem_cti_as_ferramentas_universais_internas_nao_sao_expostas():
    token = _USAR_CTI.set(False)
    try:
        ferramentas = _ferramentas_ia010()
    finally:
        _USAR_CTI.reset(token)
    nomes = {item.get("name") for item in ferramentas if item.get("type") == "function"}
    assert "catalogar_universo_cti" not in nomes
    assert "consultar_universo_cti" not in nomes


def _metadados_tabela_aplicacao():
    return {
        "fontes": [
            {
                "tipo": "WEB",
                "descricao": "Thermo King V-Series technical guide",
                "url": "https://www.thermoking.com/v-series.pdf",
            },
            {
                "tipo": "WEB",
                "descricao": "Frigo King",
                "url": "https://www.frigoking.com.br/",
            },
            {
                "tipo": "ANEXO_TEMPORARIO",
                "descricao": "TABELA DE APLICAÇÃO 2019 2.pdf",
            },
        ],
        "anexos": [
            {
                "nome": "TABELA DE APLICAÇÃO 2019 2.pdf",
                "tipo": "PDF",
                "sha256": "256e199d7c05c41ee1e4493418c5ec6a04e5af528eafdddd34419be753ab4dee",
                "estrutura": {"paginas": 1, "paginas_com_texto": 1},
                "mime_type": "application/pdf",
                "temporario": True,
                "publicado_cti": False,
                "tamanho_bytes": 242672,
            }
        ],
        "ferramentas": [{"tipo": "WEB", "fontes_encontradas": 2}],
        "web_requerida": True,
        "web_fontes_validas": 2,
        "web_urls_auditaveis": [
            "https://www.thermoking.com/v-series.pdf",
            "https://www.frigoking.com.br/",
        ],
        "somente_leitura": True,
        "controle_anexos": "temporarios_com_conhecimento_semantico_nao_operacional",
    }


def _achar(auditoria, trecho):
    for item in auditoria["afirmacoes"]:
        if trecho.casefold() in str(item.get("texto") or "").casefold():
            return item
    raise AssertionError(trecho)


def test_proveniencia_real_separa_anexo_web_controle_e_inferencia_sem_cti():
    resposta = """# Comparação de capacidades e operação

## Fatos do anexo
O arquivo anexo apresenta uma tabela de aplicação Carrier por volume e temperatura.
Viento 300, Xarios 350, Xarios 600, Supra 760 e Supra 860 aparecem na tabela do anexo.

## Fatos externos verificados (web)
A Thermo King publica guia técnico da V-Series com seleção por volume de baú.
A Frigo King possui oferta pública de equipamentos para refrigeração de transporte.

## Comparação prática
A equivalência mais segura é comparar volume, regime de temperatura e condições de aplicação sustentadas pelas fontes.

## Recomendações
Priorizar guias oficiais de fabricante antes de afirmar equivalência específica entre modelos.
"""
    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados_tabela_aplicacao(),
        pergunta_atual=PERGUNTA_REAL,
    )
    auditoria = resultado["auditoria_evidencial"]

    assert not any(item.get("tipo") == "CTI" for item in auditoria["origens_execucao"])

    titulo = _achar(auditoria, "Comparação de capacidades e operação")
    assert titulo["tipo"] == "FATO_CONTROLE"
    assert titulo["status_rastreabilidade"] == "RASTREAVEL"

    fato_anexo = _achar(auditoria, "Viento 300")
    assert fato_anexo["tipo"] == "FATO_ANEXO"
    assert fato_anexo["fontes_evidencia"] == ["ANEXO_1"]

    fato_web = _achar(auditoria, "Thermo King publica")
    assert fato_web["tipo"] == "FATO_WEB"
    assert fato_web["fontes_evidencia"]
    assert all(fonte.startswith("WEB_") for fonte in fato_web["fontes_evidencia"])

    comparacao = _achar(auditoria, "equivalência mais segura")
    assert comparacao["tipo"] == "INFERENCIA_RECOMENDACAO"
    assert "ANEXO_1" in comparacao["derivada_de"]
    assert any(fonte.startswith("WEB_") for fonte in comparacao["derivada_de"])

    recomendacao = _achar(auditoria, "Priorizar guias oficiais")
    assert recomendacao["tipo"] == "INFERENCIA_RECOMENDACAO"
    assert auditoria["totais"]["afirmacoes_sem_evidencia_explicita"] == 0
