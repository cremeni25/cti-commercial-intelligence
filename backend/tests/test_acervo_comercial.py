"""Acervo comercial: histórico preservado quando a carteira muda de mãos."""
import pytest
from fastapi import HTTPException

from services import acervo_comercial as acervo
from tests import cofre_falso, supabase_memoria


def _gatilho_banco(banco, cliente, dados):
    """Reproduz cti_sync_responsabilidade_cliente: reatribui TUDO do cliente."""
    novo = dados.get("responsavel_comercial_id")
    if not novo:
        return
    for o in banco["cti_oportunidades"]:
        if o["cliente_id"] == cliente["id"] and o.get("arquivado_em") is None:
            o["responsavel_id"] = novo
    for a in banco["cti_atividades"]:
        if a.get("cliente_id") == cliente["id"]:
            a["usuario_id"] = novo


@pytest.fixture
def banco(monkeypatch):
    dados = {
        "cti_users": [
            {"id": "ana", "nome": "Ana", "ativo": False, "status_acesso": "INATIVO", "tipo_usuario": "REPRES_REGIAO_01"},
            {"id": "beto", "nome": "Beto", "ativo": True, "status_acesso": "ATIVO", "tipo_usuario": "REPRES_REGIAO_02"},
            {"id": "gestor", "nome": "Gestor", "ativo": True, "status_acesso": "ATIVO", "tipo_usuario": "ADMIN_MASTER"},
        ],
        "clientes": [
            {"id": "c1", "nome": "Frios Alfa", "responsavel_comercial_id": "ana", "responsabilidade_tipo": "TERRITORIO"},
            {"id": "c2", "nome": "Laticínio Beta", "responsavel_comercial_id": "beto", "responsabilidade_tipo": "TERRITORIO"},
            {"id": "c3", "nome": "Sem dono", "responsavel_comercial_id": None},
        ],
        "cti_oportunidades": [
            {"id": "o-aberta", "cliente_id": "c1", "responsavel_id": "ana", "status": "PROPOSTA", "arquivado_em": None},
            {"id": "o-ganha", "cliente_id": "c1", "responsavel_id": "ana", "status": "GANHO", "arquivado_em": None},
            {"id": "o-solta", "cliente_id": "c9", "responsavel_id": "ana", "status": "OPORTUNIDADE", "arquivado_em": None},
        ],
        "cti_atividades": [
            {"id": "a-feita", "cliente_id": "c1", "oportunidade_id": "o-ganha", "usuario_id": "ana", "status": "REALIZADA"},
            {"id": "a-pendente", "cliente_id": "c1", "oportunidade_id": "o-aberta", "usuario_id": "ana", "status": "PENDENTE"},
            {"id": "a-solta", "cliente_id": None, "oportunidade_id": None, "usuario_id": "ana", "status": "PENDENTE"},
        ],
        "cti_cliente_responsabilidade_historico": [],
        "_ao_atualizar": {"clientes": [_gatilho_banco]},
    }
    monkeypatch.setattr("core.supabase_client.supabase", supabase_memoria.criar(dados))
    cofre = cofre_falso.instalar(monkeypatch)
    return dados, cofre


def _por_id(linhas):
    return {l["id"]: l for l in linhas}


def test_carteira_parada_de_quem_saiu_aparece(banco):
    resumo = acervo.carteiras()
    ana = next(p for p in resumo["pessoas"] if p["usuario_id"] == "ana")
    assert ana == {**ana, "ativo": False, "clientes": 1, "negocios_abertos": 2, "atividades_pendentes": 2}
    assert resumo["carteiras_paradas"] == 1 and resumo["clientes_sem_responsavel"] == 1
    assert resumo["pessoas"][0]["usuario_id"] == "ana"  # inativos com carteira primeiro


def test_transferencia_leva_o_aberto_e_preserva_quem_fez(banco):
    dados, cofre = banco
    resultado = acervo.transferir_carteira("ana", "beto", "saída da equipe", "gestor")
    assert resultado["clientes"] == 1 and resultado["negocios_abertos"] == 1 and resultado["atividades_pendentes"] == 1
    opp, atv = _por_id(dados["cti_oportunidades"]), _por_id(dados["cti_atividades"])
    assert opp["o-aberta"]["responsavel_id"] == "beto" and opp["o-solta"]["responsavel_id"] == "beto"
    assert opp["o-ganha"]["responsavel_id"] == "ana"  # venda fechada continua de quem fechou
    assert atv["a-pendente"]["usuario_id"] == "beto" and atv["a-solta"]["usuario_id"] == "beto"
    assert atv["a-feita"]["usuario_id"] == "ana"  # visita feita continua de quem fez
    assert _por_id(dados["clientes"])["c1"]["responsavel_comercial_id"] == "beto"
    historico = dados["cti_cliente_responsabilidade_historico"]
    assert historico[0]["responsavel_anterior_id"] == "ana" and "saída da equipe" in historico[0]["motivo"]
    # cópia de segurança antes de mexer
    assert any(n.startswith("acervo/backup-") and n.endswith(".xlsx") for n in cofre.buckets["cti-agente"])


def test_transferencia_recusa_destino_inativo_ou_mesma_pessoa(banco):
    with pytest.raises(acervo.AcervoErro):
        acervo.transferir_carteira("beto", "ana", "", "gestor")
    with pytest.raises(acervo.AcervoErro):
        acervo.transferir_carteira("beto", "beto", "", "gestor")


def test_exportacao_tem_todas_as_abas_e_nao_leva_senha(banco):
    from io import BytesIO
    from openpyxl import load_workbook

    dados, _ = banco
    dados["cti_users"][0]["senha_hash"] = "segredo"
    conteudo, totais = acervo.gerar_exportacao()
    wb = load_workbook(BytesIO(conteudo), read_only=True)
    assert {"Resumo", "Clientes", "Oportunidades", "Atividades", "Usuários", "Histórico de responsáveis"} <= set(wb.sheetnames)
    assert totais["Clientes"] == 3
    textos = {str(c) for linha in wb["Usuários"].iter_rows(values_only=True) for c in linha}
    assert "segredo" not in textos and "senha_hash" not in textos


def test_backup_listado_com_link(banco, monkeypatch):
    from services import cofre_agente

    monkeypatch.setattr(cofre_agente, "url_assinada", lambda caminho, segundos=3600: f"https://cofre/{caminho}")
    registro = acervo.salvar_backup("teste")
    lista = acervo.listar_backups()
    assert lista[0]["arquivo"] == registro["arquivo"] and lista[0]["url"].endswith(registro["arquivo"]) and lista[0]["totais"]["Clientes"] == 3


def test_rotas_so_para_gestao_e_backup_agendado_exige_token(banco, monkeypatch):
    from fastapi.testclient import TestClient
    from core.admin_auth import UsuarioAutenticado, usuario_atual
    from main import app

    cliente = TestClient(app)
    assert cliente.post("/interno/acervo/backup").status_code == 401
    assert cliente.post("/interno/acervo/backup", headers={"Authorization": "Bearer falso"}).status_code == 401

    def entrar(tipo):
        u = UsuarioAutenticado(id="u", auth_id="a", email="u@x", nome="U", tipo_usuario=tipo, permissoes={"acesso_total": tipo == "ADMIN_MASTER"})
        app.dependency_overrides[usuario_atual] = lambda: u
        monkeypatch.setattr("core.application_access.usuario_atual", lambda *a, **k: u)

    h = {"Authorization": "Bearer t"}
    try:
        entrar("REPRES_REGIAO_01")
        assert cliente.get("/crm-seguro/acervo/carteiras", headers=h).status_code == 403
        assert cliente.post("/crm-seguro/acervo/transferir", json={"de_usuario_id": "ana", "para_usuario_id": "beto"}, headers=h).status_code == 403
        entrar("ADMIN_MASTER")
        assert cliente.get("/crm-seguro/acervo/carteiras", headers=h).json()["carteiras_paradas"] == 1
        r = cliente.get("/crm-seguro/acervo/exportacao", headers=h)
        assert r.status_code == 200 and r.headers["content-type"].startswith("application/vnd.openxmlformats")
        assert cliente.post("/crm-seguro/acervo/transferir", json={"de_usuario_id": "beto", "para_usuario_id": "ana"}, headers=h).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_troca_de_responsavel_de_um_cliente_tambem_preserva_quem_fez(banco, monkeypatch):
    from core.admin_auth import UsuarioAutenticado
    from routers import crm_scope_clientes_router as rota

    dados, _ = banco
    monkeypatch.setattr(rota, "supabase", supabase_memoria.criar(dados))
    master = UsuarioAutenticado(id="gestor", auth_id="g", email="g@x", nome="G", tipo_usuario="ADMIN_MASTER", permissoes={"acesso_total": True})
    rota.definir_responsabilidade_cliente("c1", rota.ResponsabilidadeCliente(responsavel_id="beto", motivo="ajuste"), master)
    atv, opp = _por_id(dados["cti_atividades"]), _por_id(dados["cti_oportunidades"])
    assert atv["a-pendente"]["usuario_id"] == "beto" and atv["a-feita"]["usuario_id"] == "ana"
    assert opp["o-aberta"]["responsavel_id"] == "beto" and opp["o-ganha"]["responsavel_id"] == "ana"


def test_fotografia_paginada_nao_perde_autoria_com_muitos_registros(banco, monkeypatch):
    dados, _ = banco
    monkeypatch.setattr(acervo, "LIMITE_PAGINA", 2)  # força várias páginas
    for i in range(7):
        dados["cti_atividades"].append({"id": f"feita-{i}", "cliente_id": "c1", "oportunidade_id": None, "usuario_id": "ana", "status": "CONCLUIDA"})
    acervo.transferir_carteira("ana", "beto", "", "gestor")
    atv = _por_id(dados["cti_atividades"])
    assert all(atv[f"feita-{i}"]["usuario_id"] == "ana" for i in range(7))


def test_copia_nao_sai_incompleta_e_transferencia_nao_acontece(banco, monkeypatch):
    dados, _ = banco
    original = acervo.paginar

    def falha_em_pedidos(tabela, campos="*", filtro=None):
        if tabela == "cti_pedidos":
            raise RuntimeError("canceling statement due to statement timeout")
        return original(tabela, campos, filtro)

    monkeypatch.setattr(acervo, "paginar", falha_em_pedidos)
    with pytest.raises(acervo.AcervoIncompleto):
        acervo.salvar_backup("teste")
    with pytest.raises(acervo.AcervoIncompleto):
        acervo.transferir_carteira("ana", "beto", "", "gestor")
    assert _por_id(dados["clientes"])["c1"]["responsavel_comercial_id"] == "ana"  # nada mudou

    def tabela_inexistente(tabela, campos="*", filtro=None):
        if tabela == "cti_pedidos":
            raise RuntimeError("{'code': 'PGRST205', 'message': \"Could not find the table 'public.cti_pedidos'\"}")
        return original(tabela, campos, filtro)

    monkeypatch.setattr(acervo, "paginar", tabela_inexistente)
    _, totais = acervo.gerar_exportacao()  # tabela que não existe no ambiente é tolerada
    assert "Pedidos" not in totais


def test_falha_no_meio_da_troca_ainda_devolve_autoria(banco):
    dados, _ = banco

    def troca_que_cai():
        _gatilho_banco(dados, _por_id(dados["clientes"])["c1"], {"responsavel_comercial_id": "beto"})
        raise RuntimeError("conexão caiu no segundo lote")

    with pytest.raises(RuntimeError):
        acervo.trocar_responsavel_preservando(["c1"], troca_que_cai, "teste")
    assert _por_id(dados["cti_atividades"])["a-feita"]["usuario_id"] == "ana"
    assert _por_id(dados["cti_oportunidades"])["o-ganha"]["responsavel_id"] == "ana"


def test_diario_pendente_e_reparado_na_proxima_operacao(banco, monkeypatch):
    dados, cofre = banco
    foto = acervo.fotografar_autoria(["c1"])
    acervo.abrir_diario(foto, "operação interrompida")  # restauração nunca rodou
    _gatilho_banco(dados, _por_id(dados["clientes"])["c1"], {"responsavel_comercial_id": "beto"})
    assert _por_id(dados["cti_atividades"])["a-feita"]["usuario_id"] == "beto"
    assert acervo.reparar_autoria_pendente() == 1
    assert _por_id(dados["cti_atividades"])["a-feita"]["usuario_id"] == "ana"
    assert acervo.reparar_autoria_pendente() == 0  # já concluída
