from io import BytesIO

from openpyxl import Workbook

from services.universal_semantic_source import gerar_semantica


def _xlsx_bytes():
    wb = Workbook()
    ws = wb.active
    ws.title = "VENDAS"
    ws.append(["Cliente", "Equipamento", "Valor"])
    ws.append(["KONA TRANSPORTES", "X4 7500", 100000])
    ws.append(["CLIENTE B", "SUPRA 850", 80000])
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_planilha_vira_registros_semanticos_linha_a_linha():
    resultado = gerar_semantica("vendas.xlsx", "PLANILHA", _xlsx_bytes(), {})
    assert resultado["total_registros"] == 2
    assert resultado["registros"][0]["dados"]["Cliente"] == "KONA TRANSPORTES"
    assert resultado["registros"][0]["metadados"] == {"aba": "VENDAS", "linha": 2}
    assert {"Cliente", "Equipamento", "Valor"}.issubset(set(resultado["campos_semanticos"]))
    assert resultado["classificacao_sugerida"] == "COMERCIAL"


def test_texto_comercial_e_fragmentado_sem_perder_proveniencia():
    texto = ("Cliente Carrier oportunidade proposta venda pedido. " * 500).encode("utf-8")
    resultado = gerar_semantica("relatorio.txt", "TEXTO", texto, {})
    assert resultado["total_registros"] > 1
    assert resultado["classificacao_sugerida"] == "COMERCIAL"
    assert all(item["metadados"]["origem"] == "TEXTO" for item in resultado["registros"])


def test_catalogo_dinamico_e_generico_nao_depende_do_nome_do_documento(monkeypatch):
    from services import ia_comercial_fontes_dinamicas as dinamicas
    from services import ia_comercial_universo as universo

    monkeypatch.setattr(dinamicas, "_carregar_publicadas", lambda tipo: [
        {"fonte_nome_arquivo": "qualquer-nome-futuro.pdf", "conteudo_texto": "dado homologado"}
    ] if tipo == "ADMIN_MASTER" else [])
    monkeypatch.setattr(dinamicas, "_ORIGINAL_CARREGAR_FONTES", lambda usuario_id, tipo_usuario: ({}, {}))

    fontes, metadados = dinamicas._carregar_fontes_com_uploads("admin", "ADMIN_MASTER")
    assert "fontes_universais" in fontes
    assert fontes["fontes_universais"][0]["fonte_nome_arquivo"] == "qualquer-nome-futuro.pdf"
    assert metadados["fontes_universais"]["descoberta_dinamica"] is True
    assert "fontes_universais" in universo.FONTES_PUBLICAS


def test_fonte_dinamica_nao_amplia_rbac_de_outros_perfis(monkeypatch):
    from services import ia_comercial_fontes_dinamicas as dinamicas

    monkeypatch.setattr(dinamicas, "_carregar_publicadas", lambda tipo: [])
    monkeypatch.setattr(dinamicas, "_ORIGINAL_CARREGAR_FONTES", lambda usuario_id, tipo_usuario: ({}, {}))
    fontes, metadados = dinamicas._carregar_fontes_com_uploads("vendedor", "VENDEDOR")
    assert fontes["fontes_universais"] == []
    assert metadados["fontes_universais"]["autorizado"] is False
