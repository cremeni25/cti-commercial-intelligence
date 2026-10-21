"""HTTP tests against real CTI routers; Supabase transport is an explicit test double."""
from types import SimpleNamespace
import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core import admin_auth
from routers import feiras_eventos_router as feiras


class Query:
    def __init__(self, rows):
        self.rows=copy.deepcopy(rows); self.one=False
    def select(self,*a): return self
    def eq(self,k,v): self.rows=[r for r in self.rows if r.get(k)==v];return self
    def ilike(self,k,v): return self.eq(k,v)
    def in_(self,k,vs): self.rows=[r for r in self.rows if r.get(k) in vs];return self
    def order(self,*a,**kw): return self
    def limit(self,n): self.rows=self.rows[:n];return self
    def range(self,start,end): self.rows=self.rows[start:end+1];return self
    def single(self): self.one=True;return self
    def execute(self):return SimpleNamespace(data=(self.rows[0] if self.rows else None) if self.one else self.rows)


@pytest.fixture
def setup(monkeypatch):
    profiles=[dict(id=i,auth_id=i,email=i+'@example.invalid',nome=i,tipo_usuario=role,ativo=True) for i,role in [('a','AUTORIZADO_CARRIER'),('a2','AUTORIZADO_CARRIER'),('ga','GESTOR_AUTORIZADO_CARRIER'),('b','AUTORIZADO_CARRIER'),('master','ADMIN_MASTER')]]
    tables={'cti_users':profiles,'cti_user_permissions':[dict(user_id=r['id'],feiras_eventos=True) for r in profiles],
        'cti_feira_autorizadas':[dict(id='A',ativa=True),dict(id='B',ativa=True)],
        'cti_feira_profissionais':[dict(user_id=i,autorizada_id=org,papel=papel,ativo=True) for i,org,papel in [('a','A','PROFISSIONAL'),('a2','A','PROFISSIONAL'),('ga','A','GESTOR'),('b','B','PROFISSIONAL')]],
        'cti_feiras':[dict(id='fair',nome='Teste isolado')],
        'cti_feira_atendimentos':[dict(id=i,feira_id='fair',criado_por=i,autorizada_id=org,empresa=i,visitante=i,regiao='OUTRA') for i,org in [('a','A'),('a2','A'),('b','B')]],'cti_feira_itens':[]}
    db=SimpleNamespace(table=lambda name:Query(tables.get(name,[])),auth=SimpleNamespace(get_user=lambda token:SimpleNamespace(user=SimpleNamespace(id=token,email=token+'@example.invalid'))))
    monkeypatch.setattr(admin_auth,'supabase',db);monkeypatch.setattr(feiras,'supabase',db)
    app=FastAPI();app.include_router(feiras.router)
    from core.application_access import application_access
    app.middleware("http")(application_access)
    @app.get("/legacy-commercial")
    def legacy(): return {"secret": True}
    @app.get('/crm-seguro/clientes')
    def forbidden(u=__import__('fastapi').Depends(admin_auth.usuario_atual)): return {'secret':True}
    @app.get('/auth/me')
    def me(u=__import__('fastapi').Depends(admin_auth.usuario_atual)): return {'id':u.id}
    return TestClient(app),tables


def request(client,user,path): return client.get(path,headers={'Authorization':'Bearer '+user})

@pytest.mark.parametrize('user,expected',[('a',['a']),('a2',['a2']),('ga',['a','a2']),('b',['b']),('master',['a','a2','b'])])
def test_isolation_http(setup,user,expected):
    client,_=setup;r=request(client,user,'/crm-seguro/feiras/fair/atendimentos')
    assert r.status_code==200;assert sorted(x['id'] for x in r.json())==expected

@pytest.mark.parametrize('user',['a','a2','ga','b'])
def test_commercial_direct_url_denied(setup,user):
    c,_=setup;assert request(c,user,'/crm-seguro/clientes').status_code==403
    assert request(c,user,'/auth/me').status_code==200

def test_revocation_immediate(setup):
    c,t=setup;assert request(c,'a','/crm-seguro/feiras').status_code==200
    t['cti_user_permissions'][0]['feiras_eventos']=False
    assert request(c,'a','/crm-seguro/feiras').status_code==403

def test_company_revocation(setup):
    c,t=setup;t['cti_feira_autorizadas'][0]['ativa']=False
    assert request(c,'ga','/crm-seguro/feiras/fair/atendimentos').status_code==403

def test_inactive_user(setup):
    c,t=setup;t['cti_users'][0]['ativo']=False
    assert request(c,'a','/crm-seguro/feiras').status_code==403

def test_unauthenticated(setup):
    c,_=setup;assert c.get('/crm-seguro/feiras').status_code==401

def test_external_conversion_denied(setup):
    c,_=setup;r=c.post('/crm-seguro/feiras/fair/atendimentos/b/converter-oportunidade',headers={'Authorization':'Bearer a'})
    assert r.status_code==403

def test_pdf_uses_same_scope(setup):
    c,_=setup;r=request(c,'a','/crm-seguro/feiras/fair/relatorio.pdf')
    assert r.status_code==200;assert r.content.startswith(b'%PDF')


def test_pagination_http(setup):
    c,_=setup
    r=request(c,'master','/crm-seguro/feiras/fair/atendimentos?offset=1&limit=1')
    assert r.status_code==200;assert [x['id'] for x in r.json()]==['a2']
    assert request(c,'master','/crm-seguro/feiras/fair/atendimentos?limit=0').status_code==422


def test_transfer_does_not_expose_previous_company_records(setup):
    c,t=setup;t['cti_feira_profissionais'][0]['autorizada_id']='B'
    assert request(c,'a','/crm-seguro/feiras/fair/atendimentos').json()==[]


def test_legacy_route_cannot_bypass_by_omitting_token(setup):
    c,_=setup
    assert c.get('/legacy-commercial').status_code==401
    assert request(c,'a','/legacy-commercial').status_code==403
    assert request(c,'master','/legacy-commercial').status_code==200


def test_first_access_cannot_bypass_onboarding(setup):
    c,t=setup;t['cti_users'][0]['primeiro_acesso_pendente']=True
    assert request(c,'a','/crm-seguro/feiras').status_code==403
    assert request(c,'a','/auth/me').status_code==200
