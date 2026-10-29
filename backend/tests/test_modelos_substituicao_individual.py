from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.admin_auth import UsuarioAutenticado, exigir_escrita_catalogo
from routers import modelos_proposta_importacao_router as router
from routers import modelos_proposta_storage_router as storage
from routers import modelos_proposta_homologacao_router as homologacao


@pytest.fixture
def contexto(monkeypatch):
    antigos=[dict(id="m1",nome="SUPRA 750",linha_produto="DIESEL TRUCK",equipamento="SUPRA 750",versao=1,ativo=True,homologado_em="2026-01-01",arquivo_template_storage="anterior.docx",arquivo_template_hash_sha256="old")]
    tabelas={"cti_modelos_proposta":deepcopy(antigos),"cti_modelos_proposta_auditoria":[]}; uploads=[]; rpc=[]
    class Query:
        def __init__(self, nome): self.nome=nome;self.filtros=[];self.inserted=None
        def select(self,*_): return self
        def eq(self,k,v):self.filtros.append((k,v));return self
        def is_(self,k,v):self.filtros.append((k,None if v=="null" else v));return self
        @property
        def not_(self):return self
        def order(self,*_,**kw):return self
        def limit(self,*_):return self
        def insert(self,dados):self.inserted={"id":"m2",**dados};return self
        def execute(self):
            if self.inserted is not None:tabelas[self.nome].append(self.inserted);return SimpleNamespace(data=[self.inserted])
            return SimpleNamespace(data=[dict(m) for m in tabelas[self.nome] if all(m.get(k)==v for k,v in self.filtros if k!="arquivo_template_storage")])
    def upload(path, data, options):uploads.append((path,data,options));return {"path":path}
    def call_rpc(name,args):rpc.append((name,args));return SimpleNamespace(execute=lambda:SimpleNamespace(data={"id":"m1","ativo":True}))
    db=SimpleNamespace(table=Query,rpc=call_rpc,storage=SimpleNamespace(from_=lambda _:SimpleNamespace(upload=upload)))
    for modulo in (router,storage,homologacao):monkeypatch.setattr(modulo,"supabase",db)
    monkeypatch.setattr(homologacao,"_url_temporaria",lambda *_:"https://example.invalid/preview")
    app=FastAPI();app.include_router(router.router);app.include_router(homologacao.router)
    app.dependency_overrides[exigir_escrita_catalogo]=lambda:UsuarioAutenticado(id="master",auth_id="auth",email="unit@example.invalid",nome="Master",tipo_usuario="ADMIN_MASTER")
    return TestClient(app),tabelas,uploads,rpc,antigos


def docx():
    b=BytesIO()
    with ZipFile(b,"w") as z:z.writestr("[Content_Types].xml","<Types/>");z.writestr("word/document.xml","<document>Documento novo</document>")
    return b.getvalue()


def test_upload_preserva_original_e_registra_nova_versao_inativa(contexto):
    c,t,uploads,_,antigos=contexto;arquivo=docx()
    r=c.post("/modelos-proposta-importacao/substituir/m1",files={"arquivo":("novo.docx",arquivo)})
    assert r.status_code==200
    assert t["cti_modelos_proposta"][0]==antigos[0]
    novo=t["cti_modelos_proposta"][1]
    assert novo["versao"]==2 and novo["ativo"] is False and novo["homologado_em"] is None
    assert uploads[0][1]==arquivo and uploads[0][2]["upsert"]=="false"
    assert t["cti_modelos_proposta_auditoria"][0]["operacao"]=="NOVA_VERSAO"


def test_zip_que_nao_e_word_nao_cria_versao(contexto):
    c,t,uploads,_,_=contexto;b=BytesIO()
    with ZipFile(b,"w") as z:z.writestr("qualquer.txt","não é Word")
    assert c.post("/modelos-proposta-importacao/substituir/m1",files={"arquivo":("novo.docx",b.getvalue())}).status_code==422
    assert not uploads and len(t["cti_modelos_proposta"])==1


def test_ativacao_exige_homologacao_antes_de_invocar_transacao(contexto):
    c,t,_,rpc,_=contexto;t["cti_modelos_proposta"][0]["homologado_em"]=None
    assert c.post("/modelos-proposta-importacao/ativar/m1").status_code==409
    assert not rpc


def test_ativacao_verifica_binario_e_delega_transacao(contexto,monkeypatch):
    c,_,_,rpc,_=contexto;verificados=[]
    monkeypatch.setattr(storage,"_baixar_e_validar_arquivo_armazenado",lambda m:verificados.append(m["id"]))
    assert c.post("/modelos-proposta-importacao/ativar/m1").status_code==200
    assert verificados==["m1"]
    assert rpc[0][0]=="cti_ativar_modelo_proposta" and rpc[0][1]["p_sha256"]=="old"


def test_fila_inclui_nova_versao_inativa(contexto):
    c,t,_,_,_=contexto;t["cti_modelos_proposta"].append(dict(id="m2",equipamento="SUPRA 750",versao=2,ativo=False,homologado_em=None,arquivo_template_storage="novo.docx"))
    r=c.get("/modelos-proposta-homologacao/fila")
    assert r.status_code==200 and [m["id"] for m in r.json()["fila"]]==["m2"]


def test_gestao_nao_e_publica():
    app=FastAPI();app.include_router(router.router);c=TestClient(app)
    assert c.get("/modelos-proposta-importacao/versoes").status_code==401
    assert c.post("/modelos-proposta-importacao/ativar/m1").status_code==401
