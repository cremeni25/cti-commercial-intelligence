"""Consulta cadastral: contrato HTTP, isolamento e preservação de dados locais."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers import crm_app_cnpj_router as cnpj

CNPJ = "00000000000191"


@pytest.fixture
def contexto(monkeypatch):
    tabelas = {"clientes": [], "cti_clientes": []}
    fontes = []
    usuario = UsuarioAutenticado(id="vendedor", auth_id="auth", email="teste@example.invalid", nome="Teste", tipo_usuario="USUARIO_CTI", permissoes={"clientes_editar": True})

    class Query:
        def __init__(self, tabela):
            self.tabela = tabela
        def select(self, *_): return self
        def in_(self, campo, valores):
            self.campo, self.valores = campo, valores
            return self
        def limit(self, *_): return self
        def execute(self):
            dados = tabelas[self.tabela]
            if isinstance(dados, Exception): raise dados
            return SimpleNamespace(data=[dict(r) for r in dados if r.get(self.campo) in self.valores][:1])

    def publico(valor):
        fontes.append(valor)
        return {"ok": True, "dados": {"nome": "Nome da fonte", "endereco": "Rua da fonte", "numero": "100", "cidade": "Cidade da fonte", "estado": "SP", "cnpj": CNPJ, "fonte": "Fonte pública"}}

    monkeypatch.setattr(cnpj, "supabase", SimpleNamespace(table=Query))
    monkeypatch.setattr(cnpj, "consultar_cnpj_publico", publico)
    app = FastAPI()
    app.include_router(cnpj.router)
    app.dependency_overrides[usuario_atual] = lambda: usuario
    return TestClient(app), tabelas, fontes


def test_existente_retorna_campos_e_aliases_sem_expor_dados_internos(contexto):
    client, tabelas, fontes = contexto
    tabelas["clientes"] = [{"id": "c1", "cnpj": "00.000.000/0001-91", "razao_social": "Cliente", "logradouro": "Rua salva", "numero": "9", "bairro": "Centro", "municipio": "Cidade", "uf": "SP", "telefone": "11999990000", "cep": "01001000", "email": "cliente@example.invalid", "responsavel_comercial_id": "vendedor", "anotacao_interna": "privada"}]
    r = client.get(f"/crm-app/clientes/cnpj/{CNPJ}")
    assert r.status_code == 200
    dados = r.json()["cliente"]
    assert dados["endereco"] == "Rua salva"
    assert dados["numero"] == "9"
    assert dados["cidade"] == "Cidade"
    assert dados["fone"] == "11999990000"
    assert dados["cnpj"] == CNPJ
    assert "anotacao_interna" not in dados
    assert fontes == []


def test_edicao_complementa_sem_sobrescrever_e_sem_gravar(contexto):
    client, tabelas, fontes = contexto
    original = {"id": "c1", "cnpj": CNPJ, "nome": "Nome salvo", "endereco": "Rua salva", "cidade": "Cidade salva", "responsavel_comercial_id": "vendedor"}
    tabelas["clientes"] = [original]
    r = client.get(f"/crm-app/clientes/cnpj/{CNPJ}?cliente_id=c1")
    assert r.status_code == 200
    assert r.json()["cliente"]["nome"] == "Nome salvo"
    assert r.json()["cliente"]["endereco"] == "Rua salva"
    assert r.json()["cliente"]["numero"] == "100"
    assert fontes == [CNPJ]
    assert tabelas["clientes"] == [original]
    assert "numero" not in original


def test_cliente_de_outra_carteira_nao_expoe_cadastro(contexto):
    client, tabelas, fontes = contexto
    tabelas["clientes"] = [{"id": "c2", "cnpj": CNPJ, "responsavel_comercial_id": "outro", "email": "privado@example.invalid"}]
    r = client.get(f"/crm-app/clientes/cnpj/{CNPJ}?cliente_id=c2")
    assert r.status_code == 403
    assert "privado" not in r.text
    assert fontes == []


def test_cnpj_invalido_nao_consulta_fontes(contexto):
    client, _, fontes = contexto
    assert client.get("/crm-app/clientes/cnpj/123").status_code == 422
    assert fontes == []


def test_falha_canonica_nao_parece_cadastro_inexistente(contexto):
    client, tabelas, fontes = contexto
    tabelas["clientes"] = APIError({"code": "PGRST205", "message": "missing", "details": None, "hint": None})
    assert client.get(f"/crm-app/clientes/cnpj/{CNPJ}").status_code == 503
    assert fontes == []


def test_fonte_legada_ausente_permite_consulta_publica(contexto):
    client, tabelas, fontes = contexto
    tabelas["cti_clientes"] = APIError({"code": "PGRST205", "message": "missing", "details": None, "hint": None})
    r = client.get(f"/crm-app/clientes/cnpj/{CNPJ}")
    assert r.status_code == 200
    assert r.json()["status"] == "ENCONTRADO"
    assert fontes == [CNPJ]


def test_sem_sessao_nao_consulta_cadastro():
    app = FastAPI()
    app.include_router(cnpj.router)
    assert TestClient(app).get(f"/crm-app/clientes/cnpj/{CNPJ}").status_code == 401


def test_visualizacao_proposta_prioriza_cadastro_canonico(monkeypatch):
    from routers import propostas_consulta_router as propostas
    tabelas = {"clientes": [{"id": "c1", "nome": "Cliente atualizado", "endereco": "Rua salva"}], "cti_clientes": [{"id": "c1", "nome": "Cliente antigo"}]}
    class Consulta:
        def __init__(self, tabela): self.tabela = tabela
        def select(self, *_): return self
        def eq(self, campo, valor): self.campo, self.valor = campo, valor; return self
        def limit(self, *_): return self
        def execute(self): return SimpleNamespace(data=[r for r in tabelas[self.tabela] if r.get(self.campo) == self.valor])
    monkeypatch.setattr(propostas, "supabase", SimpleNamespace(table=Consulta))
    assert propostas._buscar_cliente({"cliente_id": "c1"})["endereco"] == "Rua salva"
    tabelas["clientes"] = []
    assert propostas._buscar_cliente({"cliente_id": "c1"})["nome"] == "Cliente antigo"
