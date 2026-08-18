from services import ia_comercial_agente_crm as crm
from services.ia_comercial_conhecimento_semantico import eh_dominio_frio
from services.ia_comercial_ia010_continuidade import (
    _USAR_CTI,
    _ferramentas_ia010,
    _fontes_requeridas_ia010,
)
from services.ia_comercial_auditoria_proveniencia import construir_auditoria_evidencial


def test_documento_com_concorrentes_exige_web_sem_forcar_cti():
    pergunta = (
        "Analise o arquivo e compare com o que os concorrentes da Carrier Transicold Brasil "
        "estão ofertando ao mercado, pontuando pontos positivos e negativos relativos ao nosso produto"
    )
    assert _fontes_requeridas_ia010(pergunta) == {"web"}


def test_cti_so_entra_quando_pedido_interno_e_relevante():
    assert _fontes_requeridas_ia010("Este cliente já existe no CRM do CTI?") == {"universo_cti"}
    assert _fontes_requeridas_ia010("Compare nossas vendas registradas com o mercado atual") == {
        "universo_cti",
        "web",
    }


def test_ferramentas_internas_sao_ocultadas_quando_cti_nao_e_requerido():
    token = _USAR_CTI.set(False)
    try:
        ferramentas = _ferramentas_ia010()
    finally:
        _USAR_CTI.reset(token)
    nomes = {item.get("name") for item in ferramentas if item.get("type") == "function"}
    assert "catalogar_universo_cti" not in nomes
    assert "consultar_universo_cti" not in nomes


def test_anexo_lynx_e_reconhecido_como_conhecimento_da_cadeia_fria():
    anexo = {
        "nome": "Telemetria Carrier - LYNX FLEET 2026.pdf",
        "conteudo_extraido": "Cadeia do frio conectada. Monitoramento de temperatura, telemetria e comando remoto 2-way.",
    }
    assert eh_dominio_frio(anexo, "Compare com concorrentes") is True


def test_documento_estranho_ao_dominio_nao_e_promovido_semanticamente():
    anexo = {
        "nome": "receita_de_bolo.txt",
        "conteudo_extraido": "Misture farinha, açúcar e ovos e leve ao forno.",
    }
    assert eh_dominio_frio(anexo, "Resuma o arquivo") is False


def _metadados_lynx():
    return {
        "fontes": [
            {"tipo": "WEB", "descricao": "Connected Solutions - Thermo King", "url": "https://example.com/tk"},
            {"tipo": "ANEXO_TEMPORARIO", "descricao": "Telemetria Carrier - LYNX FLEET 2026.pdf"},
        ],
        "anexos": [
            {
                "nome": "Telemetria Carrier - LYNX FLEET 2026.pdf",
                "tipo": "PDF",
                "sha256": "2294a9327d23438d7357e166cfae67365567096d9ea01c55da8c6f8323400b79",
                "estrutura": {"paginas": 21, "paginas_com_texto": 20},
                "mime_type": "application/pdf",
                "temporario": True,
                "publicado_cti": False,
                "tamanho_bytes": 2561222,
            }
        ],
        "ferramentas": [{"tipo": "WEB", "fontes_encontradas": 1}],
        "web_requerida": True,
        "web_fontes_validas": 1,
        "web_urls_auditaveis": ["https://example.com/tk"],
        "somente_leitura": True,
        "controle_anexos": "temporarios_com_conhecimento_semantico_nao_operacional",
    }


def _achar(auditoria, trecho):
    for item in auditoria["afirmacoes"]:
        if trecho.casefold() in str(item.get("texto") or "").casefold():
            return item
    raise AssertionError(trecho)


def test_transicao_web_anexo_recomendacao_e_metatexto_ficam_corretos():
    resposta = """A pergunta original foi: analise o arquivo e compare com concorrentes.
Nesta execução, as evidências externas disponíveis permitem o seguinte:

## 2) Fatos externos verificados (web) — concorrentes
A Thermo King oferta solução conectada de telemetria.

## 3) Análise do arquivo (o que ele contém) — evidência do anexo
O PDF anexo descreve o BLUEDGE LYNX FLEET.
**comando remoto (2-way)** para alterar parâmetros e resetar alarmes.

## 5) Recomendações (inferências acionáveis, sem inventar dados)
Preparar um comparativo comercial focado em comando remoto e integração.
"""
    resultado = construir_auditoria_evidencial(
        resposta_texto=resposta,
        metadados=_metadados_lynx(),
        pergunta_atual="Analise o arquivo e compare com concorrentes",
    )
    auditoria = resultado["auditoria_evidencial"]

    controle = _achar(auditoria, "A pergunta original")
    assert controle["tipo"] == "FATO_CONTROLE"
    assert controle["status_rastreabilidade"] == "RASTREAVEL"

    fato_web = _achar(auditoria, "Thermo King oferta")
    assert fato_web["tipo"] == "FATO_WEB"

    fato_anexo = _achar(auditoria, "BLUEDGE LYNX FLEET")
    assert fato_anexo["tipo"] == "FATO_ANEXO"
    assert fato_anexo["fontes_evidencia"] == ["ANEXO_1"]

    recomendacao = _achar(auditoria, "Preparar um comparativo")
    assert recomendacao["tipo"] == "INFERENCIA_RECOMENDACAO"
