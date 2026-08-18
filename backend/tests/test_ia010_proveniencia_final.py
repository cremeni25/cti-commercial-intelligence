from services import ia_comercial_ia010_proveniencia_final  # noqa: F401
from services.ia_comercial_auditoria_proveniencia import construir_auditoria_evidencial


def _achar(auditoria, trecho):
    for item in auditoria["afirmacoes"]:
        if trecho.casefold() in str(item.get("texto") or "").casefold():
            return item
    raise AssertionError(trecho)


def _metadados():
    return {
        "fontes": [
            {"tipo": "WEB", "descricao": "Thermo King V-300", "url": "https://example.com/tk"},
            {"tipo": "ANEXO_TEMPORARIO", "descricao": "TABELA DE APLICAÇÃO 2019 2.pdf"},
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
        "ferramentas": [{"tipo": "WEB", "fontes_encontradas": 1}],
        "web_requerida": True,
        "web_fontes_validas": 1,
        "web_urls_auditaveis": ["https://example.com/tk"],
        "somente_leitura": True,
        "controle_anexos": "temporarios_com_conhecimento_semantico_nao_operacional",
    }


def test_titulo_real_o_que_o_seu_arquivo_mantem_lista_em_anexo():
    resposta = """Comparei as capacidades do PDF com dados verificados na web.

## 1) O que o seu arquivo (Carrier) traz — base de comparação
No PDF interno aparecem os modelos Carrier:
- **VIENTO 300 (R404A)**
- **XARIOS 350 (R404A)**
- **XARIOS 600 (R404A)**
- **SUPRA 760 (R404A)**
- **SUPRA 860 (R404A)**
E a tabela associa tamanho de baú (m³) e temperaturas de aplicação.

## 2) Thermo King — dados encontrados na web
A Thermo King publica dados do V-300. https://example.com/tk
"""
    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados(),
        pergunta_atual="Compare as capacidades e busque em Frigoking e Thermo King quais as equivalências em capacidade e operação.",
    )
    auditoria = resultado["auditoria_evidencial"]

    for trecho in (
        "VIENTO 300",
        "XARIOS 350",
        "XARIOS 600",
        "SUPRA 760",
        "SUPRA 860",
        "tabela associa tamanho de baú",
    ):
        item = _achar(auditoria, trecho)
        assert item["tipo"] == "FATO_ANEXO"
        assert item["fontes_evidencia"] == ["ANEXO_1"]

    web = _achar(auditoria, "Thermo King publica")
    assert web["tipo"] == "FATO_WEB"
    assert resultado["auditoria_afirmacoes_sem_evidencia"] == 0
