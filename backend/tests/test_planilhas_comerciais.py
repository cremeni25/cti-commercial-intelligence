"""Carga cifrada do funil e das NEGOCIAÇÕES (dados fictícios; nada real no repositório)."""
import gzip
import io
import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from parsers.planilha_negociacoes import ler_negociacoes
from services import cofre_cifrado, ia_comercial_universo, planilhas_comerciais
from tests import cofre_falso
from tests.test_historical_sales_funnel import _fixture as funil_ficticio


def _negociacoes_ficticias() -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    wb.create_sheet("LYNX")
    andamento = wb.create_sheet("EM ANDAMENTO")
    andamento.append(["COD", "DATA ", "VENDEDOR", "CLIENTE ", "CNPJ ", "CONTATO ", "EQUIP", "MODELO", "QTDE", "VALOR  UN", "INSTALAÇÃO ", "TOTAL ", "PAGTO", "IMPOSTO", "INSTALAÇÃO ", "VENDA", "INDICAÇÃO", "follow-up", "STATUS", "ANOTAÇÕES", "CASO SC", "CADASTRO", "credito", "BAIXA"])
    andamento.append([10, datetime(2026, 10, 1), "ANDERSON", "Transportes Alfa", "00.000.000/0001-00", "Fulano", "DD", "CITIMAX 500", 2, 30000, 1000, 62000, "A VISTA", None, "RV", "RV", None, datetime(2026, 10, 9), "AGUARDANDO CRÉDITO", "nota interna", None, None, None, "CARRIER"])
    andamento.append([11, datetime(2026, 10, 2), "ANDRE ", "", None, None, "DT", "SUPRA 850"])  # sem cliente: ignorada
    vendas = wb.create_sheet("VENDAS ")  # nome real tem espaço no fim
    vendas.append(["MÊS", "PENDENCIA", "CÓD NEG", "Cliente", None, "Equipamento", "QTDE", "R$ Unitário", "R$ INSTALAÇÃO", "Forma de pgto", "VENDA", "NF Carrier", "DATA EMISSÃO", None, None, None, "DATA INSTALAÇÃO", "INSTALADOR", "SÉRIE", "CG", None, None, "VENDEDOR"])
    vendas.append([datetime(2026, 9, 1), "FINALIZADO", "9", "Frios Beta", "TR", "X4 7500", 1, 124800, 0, "5X", "RV", 123, datetime(2026, 9, 3), None, None, None, datetime(2026, 9, 10), "RV", "SERIE-X", 1, None, None, "ANDRE"])
    saida = io.BytesIO()
    wb.save(saida)
    return saida.getvalue()


@pytest.fixture
def cofre(monkeypatch, tmp_path):
    storage = cofre_falso.instalar(monkeypatch)
    monkeypatch.setattr(cofre_cifrado, "_cache_privada", None)
    monkeypatch.setattr(planilhas_comerciais, "ARQUIVO_PACOTE", tmp_path / "pacote-comercial.json")
    planilhas_comerciais.limpar_cache()
    yield storage
    planilhas_comerciais.limpar_cache()


def _gravar_pacote(tmp_path):
    funil = funil_ficticio(tmp_path)
    pacote = planilhas_comerciais.montar_pacote(("funil.xlsx", funil.read_bytes()), ("NEGOCIAÇÕES.xlsx", _negociacoes_ficticias()), "TESTE")
    envelope = cofre_cifrado.cifrar(planilhas_comerciais.compactar(pacote), cofre_cifrado.chave_publica_b64(), planilhas_comerciais.ROTULO)
    planilhas_comerciais.ARQUIVO_PACOTE.write_text(json.dumps(envelope), encoding="utf-8")
    return pacote, envelope


def test_leitor_negociacoes_mantem_negocio_e_descarta_dado_pessoal():
    dados = ler_negociacoes(_negociacoes_ficticias())
    assert len(dados["negociacoes_andamento"]) == 1 and len(dados["vendas_realizadas"]) == 1
    negocio = dados["negociacoes_andamento"][0]
    assert negocio["vendedor"] == "ANDERSON - VIENA SP" and negocio["follow_up"] == "2026-10-09" and negocio["status"] == "AGUARDANDO CRÉDITO"
    assert "contato" not in negocio and "nota interna" not in json.dumps(negocio, ensure_ascii=False)
    venda = dados["vendas_realizadas"][0]
    assert venda["valor_total_equipamento"] == 124800 and venda["vendedor"] == "ANDRE - VIENA SP" and venda["mes"] == "2026-09-01"
    assert "SERIE-X" not in json.dumps(venda)  # série/NF/comissão ficam fora


def test_chave_criada_uma_vez_e_privada_so_no_cofre_privado(cofre):
    publica = cofre_cifrado.chave_publica_b64()
    cofre_cifrado._cache_privada = None
    assert cofre_cifrado.chave_publica_b64() == publica
    assert cofre.publicos["cti-agente"] is False and cofre_cifrado.CAMINHO_CHAVE in cofre.buckets["cti-agente"]


def test_pacote_cifrado_nao_e_legivel_e_abre_no_backend(cofre, tmp_path):
    pacote, envelope = _gravar_pacote(tmp_path)
    bruto = planilhas_comerciais.ARQUIVO_PACOTE.read_text(encoding="utf-8")
    for texto in ("Transportes Alfa", "Frios Beta", "Cliente A"):
        assert texto not in bruto
    assert pacote["totais"] == {"funil_vendas_atual": 3, "negociacoes_andamento": 1, "vendas_realizadas": 1}
    resumo = planilhas_comerciais.resumo()
    assert resumo["disponivel"] and resumo["totais"]["vendas_realizadas"] == 1 and resumo["vendas_por_ano"] == {"2026": 1}


def test_envelope_adulterado_ou_de_outra_chave_nao_abre(cofre, tmp_path):
    _, envelope = _gravar_pacote(tmp_path)
    adulterado = dict(envelope, rotulo="outro")
    with pytest.raises(cofre_cifrado.EnvelopeInvalido):
        cofre_cifrado.abrir(adulterado)
    cofre_cifrado._cache_privada = None
    cofre.buckets["cti-agente"].pop(cofre_cifrado.CAMINHO_CHAVE)  # chave nova ≠ chave da carga
    planilhas_comerciais.limpar_cache()
    assert planilhas_comerciais.carregar_pacote() is None
    assert planilhas_comerciais.resumo()["disponivel"] is False


def test_sem_pacote_fontes_ficam_vazias_sem_erro(cofre):
    assert planilhas_comerciais.registros("vendas_realizadas") == []
    assert planilhas_comerciais.resumo() == {"disponivel": False, "erro": None}


def test_ia_ve_planilhas_somente_admin_master(cofre, tmp_path, monkeypatch):
    from services import ia_comercial_fonte_planilhas as fonte

    _gravar_pacote(tmp_path)
    monkeypatch.setattr(fonte, "_ORIGINAL", lambda usuario_id, tipo: ({}, {}))
    master, meta = fonte._carregar_fontes_com_planilhas("u1", "ADMIN_MASTER")
    assert len(master["vendas_realizadas"]) == 1 and len(master["negociacoes_andamento"]) == 1 and len(master["funil_vendas_atual"]) == 3
    vendedor, meta_v = fonte._carregar_fontes_com_planilhas("u2", "REPRES_REGIAO_01")
    assert all(vendedor[f] == [] for f in fonte.FONTES) and meta_v["vendas_realizadas"]["autorizado"] is False
    assert set(fonte.FONTES) <= set(ia_comercial_universo.FONTES_PUBLICAS)


def test_rotas_chave_publica_aberta_e_resumo_so_gestao(cofre, monkeypatch):
    from core.admin_auth import UsuarioAutenticado, usuario_atual
    from main import app

    cliente = TestClient(app)
    resposta = cliente.get("/ingestao-cifrada/chave-publica")
    assert resposta.status_code == 200 and resposta.json()["chave_publica"] == cofre_cifrado.chave_publica_b64()
    assert "privada" not in resposta.text

    def entrar(tipo):
        usuario = UsuarioAutenticado(id="u", auth_id="a", email="u@x", nome="U", tipo_usuario=tipo, permissoes={"acesso_total": tipo == "ADMIN_MASTER"})
        app.dependency_overrides[usuario_atual] = lambda: usuario
        monkeypatch.setattr("core.application_access.usuario_atual", lambda *a, **k: usuario)

    try:
        entrar("REPRES_REGIAO_01")
        assert cliente.get("/crm-seguro/planilhas-comerciais/resumo", headers={"Authorization": "Bearer t"}).status_code == 403
        entrar("ADMIN_MASTER")
        assert cliente.get("/crm-seguro/planilhas-comerciais/resumo", headers={"Authorization": "Bearer t"}).json()["disponivel"] is False
    finally:
        app.dependency_overrides.clear()


def test_carga_pelo_cti_vai_para_o_cofre_e_mantem_a_outra_planilha(cofre, tmp_path):
    funil = funil_ficticio(tmp_path).read_bytes()
    resumo = planilhas_comerciais.atualizar_pacote(None, ("NEGOCIAÇÕES.xlsx", _negociacoes_ficticias()), "master")
    assert resumo["totais"] == {"funil_vendas_atual": 0, "negociacoes_andamento": 1, "vendas_realizadas": 1}
    resumo = planilhas_comerciais.atualizar_pacote(("funil.xlsx", funil), None, "master")
    assert resumo["totais"] == {"funil_vendas_atual": 3, "negociacoes_andamento": 1, "vendas_realizadas": 1}
    assert {a["tipo"] for a in resumo["arquivos"]} == {"FUNIL_VENDAS", "NEGOCIACOES"}
    bruto = cofre.buckets["cti-agente"][planilhas_comerciais.COFRE_PACOTE]
    assert b"Transportes Alfa" not in bruto  # compactado, em bucket privado
    planilhas_comerciais.limpar_cache()  # outra instância do backend lê do cofre
    assert len(planilhas_comerciais.registros("vendas_realizadas")) == 1


def test_rota_de_carga_somente_master_e_valida_arquivo(cofre, monkeypatch):
    from core.admin_auth import UsuarioAutenticado, usuario_atual
    from main import app

    cliente = TestClient(app)

    def entrar(tipo, acesso_total=False):
        usuario = UsuarioAutenticado(id="u", auth_id="a", email="u@x", nome="U", tipo_usuario=tipo, permissoes={"acesso_total": acesso_total})
        app.dependency_overrides[usuario_atual] = lambda: usuario
        monkeypatch.setattr("core.application_access.usuario_atual", lambda *a, **k: usuario)

    cabecalho = {"Authorization": "Bearer t"}
    neg = {"negociacoes": ("NEGOCIAÇÕES.xlsx", _negociacoes_ficticias(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    try:
        entrar("DIRETOR_VIENA_SP", acesso_total=True)
        assert cliente.post("/crm-seguro/planilhas-comerciais/carga", files=neg, headers=cabecalho).status_code == 403
        entrar("ADMIN_MASTER", acesso_total=True)
        assert cliente.post("/crm-seguro/planilhas-comerciais/carga", files={"negociacoes": ("n.pdf", b"x", "application/pdf")}, headers=cabecalho).status_code == 415
        assert cliente.post("/crm-seguro/planilhas-comerciais/carga", files={"negociacoes": ("n.xlsx", b"nao e zip", "application/octet-stream")}, headers=cabecalho).status_code == 422
        resposta = cliente.post("/crm-seguro/planilhas-comerciais/carga", files=neg, headers=cabecalho)
        assert resposta.status_code == 200 and resposta.json()["totais"]["vendas_realizadas"] == 1
        assert cliente.get("/crm-seguro/planilhas-comerciais/resumo", headers=cabecalho).json()["disponivel"] is True
    finally:
        app.dependency_overrides.clear()
