from services import ia_comercial_anexos as anexos
from services import ia_comercial_ia010_auditoria_operacional_final  # noqa: F401
from services.ia_comercial_auditoria_proveniencia import construir_auditoria_evidencial


class _PaginaSemTexto:
    def extract_text(self):
        return ""


class _LeitorSemTexto:
    def __init__(self, _stream):
        self.pages = [_PaginaSemTexto()]


def test_pdf_sem_camada_textual_usa_extracao_visual(monkeypatch):
    monkeypatch.setattr(anexos, "PdfReader", _LeitorSemTexto)
    monkeypatch.setattr(
        anexos,
        "extrair_pdf_visual",
        lambda _conteudo, _nome: "| Modelo | Volume |\n| Viento 300 | 18 m³ |",
    )

    texto, estrutura = anexos._ler_pdf(b"pdf-visual", "TABELA DE APLICACAO.pdf")

    assert "Viento 300" in texto
    assert estrutura["paginas"] == 1
    assert estrutura["paginas_com_texto"] == 0
    assert estrutura["conteudo_extraido_disponivel"] is True
    assert estrutura["modo_extracao"] == "visual_openai"
    assert estrutura["extracao_visual"] is True


def _metadados():
    return {
        "fontes": [
            {"tipo": "WEB", "descricao": "Thermo King V Series", "url": "https://thermoking.example/v-series.pdf"},
            {"tipo": "WEB", "descricao": "Frigo King Flex", "url": "https://frigoking.example/flex"},
            {"tipo": "ANEXO_TEMPORARIO", "descricao": "TABELA DE APLICAÇÃO.pdf"},
        ],
        "anexos": [
            {
                "nome": "TABELA DE APLICAÇÃO.pdf",
                "tipo": "PDF",
                "sha256": "abc123",
                "estrutura": {"paginas": 1, "paginas_com_texto": 0, "modo_extracao": "visual_openai"},
                "mime_type": "application/pdf",
                "temporario": True,
                "publicado_cti": False,
                "tamanho_bytes": 123,
            }
        ],
        "ferramentas": [{"tipo": "WEB", "fontes_encontradas": 2}],
        "web_requerida": True,
        "web_fontes_validas": 2,
        "web_urls_auditaveis": ["https://thermoking.example/v-series.pdf", "https://frigoking.example/flex"],
        "somente_leitura": True,
        "controle_anexos": "temporarios_com_conhecimento_semantico_nao_operacional",
    }


def _achar(auditoria, trecho):
    for item in auditoria["afirmacoes"]:
        if trecho.casefold() in str(item.get("texto") or "").casefold():
            return item
    raise AssertionError(trecho)


def test_auditoria_herda_fonte_web_e_separa_inferencia_controle():
    resposta = """## 1) Thermo King: referência objetiva por capacidade/volume
Guia oficial: https://thermoking.example/v-series.pdf
- **V-100**: 12 m³ | 5 m³
- **V-200**: 18 m³ | 9 m³

## 2) Frigo King: o que dá para afirmar agora
Linha Flex oficial: https://frigoking.example/flex
- **Flex S** integra a linha Flex.

## 3) Como eu estruturaria a equivalência em capacidade e operação (o método correto)
- A equivalência deve separar resfriado e congelado.

## 4) Para eu finalizar o comparativo como você pediu, me confirme 1 coisa
Você quer equivalência para qual classe de aplicação?
"""
    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados(),
        pergunta_atual="Compare e busque em Frigo King e Thermo King.",
    )
    auditoria = resultado["auditoria_evidencial"]

    assert _achar(auditoria, "V-100")["tipo"] == "FATO_WEB"
    assert _achar(auditoria, "V-100")["fontes_evidencia"] == ["WEB_1"]
    assert _achar(auditoria, "V-200")["fontes_evidencia"] == ["WEB_1"]
    assert _achar(auditoria, "Flex S")["fontes_evidencia"] == ["WEB_2"]
    assert _achar(auditoria, "equivalência deve separar")["tipo"] == "INFERENCIA_RECOMENDACAO"
    assert _achar(auditoria, "Você quer equivalência")["tipo"] == "FATO_CONTROLE"
    assert resultado["auditoria_afirmacoes_sem_evidencia"] == 0
