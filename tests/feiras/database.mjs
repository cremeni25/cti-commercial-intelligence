import { PGlite } from '@electric-sql/pglite'
import { readFileSync,writeFileSync } from 'node:fs'
import assert from 'node:assert/strict'
const db=new PGlite()
await db.exec(`
create role anon;create role authenticated;create role service_role bypassrls;
create table cti_users (id uuid primary key default gen_random_uuid(),auth_id uuid,email text,nome text,empresa text,cargo text,funcao text,tipo_usuario text,territorio text,ddds text[],gestor_responsavel text,superior_id uuid,ativo boolean,status_acesso text,primeiro_acesso_pendente boolean,cadastro_completo boolean,senha_temporaria_criada_em timestamptz,created_at timestamptz,updated_at timestamptz);
create table cti_user_permissions (user_id uuid primary key references cti_users(id),acesso_portal boolean,acesso_crm boolean,acesso_total boolean,feiras_eventos boolean,updated_at timestamptz,created_at timestamptz);
create table cti_feiras(id uuid primary key,nome text);
create table cti_feira_atendimentos (id uuid primary key default gen_random_uuid(),feira_id uuid references cti_feiras(id),empresa text,cnpj text,visitante text,contato text,email text,cidade text,uf text,regiao text,autorizado_destino text,interesse text,observacoes text,moeda text,valor_referencia numeric,criado_por text,criado_em timestamptz default now(),status text default 'REGISTRADO');
create table cti_feira_itens(id uuid primary key default gen_random_uuid(),atendimento_id uuid references cti_feira_atendimentos(id) on delete cascade,codigo_produto text,linha_produto text,nome_produto text,quantidade integer check(quantidade>0),lancamento_feira boolean,descricao_lancamento text);
`)
await db.exec(readFileSync(new URL('../../supabase/migrations/20261021101633_feiras_transacoes_isolamento.sql',import.meta.url),'utf8'))
// Reapplication must preserve schema and data.
await db.exec(readFileSync(new URL('../../supabase/migrations/20261021101633_feiras_transacoes_isolamento.sql',import.meta.url),'utf8'))
const uuid=n=>`00000000-0000-4000-8000-${String(n).padStart(12,'0')}`
await db.query(`insert into cti_feiras values($1,'Feira de teste isolada')`,[uuid(1)])
await db.query(`insert into cti_feira_autorizadas(id,nome) values($1,'Autorizada A'),($2,'Autorizada B')`,[uuid(2),uuid(3)])
const permissions={acesso_portal:true,acesso_crm:true,acesso_total:true,feiras_eventos:true}
const provision=async(n,org,papel='PROFISSIONAL')=>(await db.query('select cti_feira_provisionar(null,$1,$2,$3,$4) as r',[JSON.stringify({auth_id:uuid(n+1000),nome:'Profissional teste '+n,email:`p${n}@example.invalid`,empresa:'Teste',ativo:true,tipo_usuario:'USUARIO_CTI'}),JSON.stringify(permissions),org,papel])).rows[0].r
const a=await provision(10,uuid(2)),a2=await provision(11,uuid(2)),gestor=await provision(12,uuid(2),'GESTOR'),b=await provision(13,uuid(3))
assert.equal(a.permissoes.acesso_total,false);assert.equal(a.permissoes.acesso_portal,false)
assert.equal(gestor.tipo_usuario,'GESTOR_AUTORIZADO_CARRIER')
const payload=k=>({feira_id:uuid(1),empresa:'Visitante teste',visitante:'Contato isolado',regiao:'OUTRA',client_request_id:k})
const itens=[{codigo_produto:'C1',linha_produto:'Truck',nome_produto:'Equipamento',quantidade:1,lancamento_feira:false}]
const registrar=async(user,p,i=itens)=>(await db.query('select cti_feira_registrar($1,$2,$3) as r',[user,JSON.stringify(p),JSON.stringify(i)])).rows[0].r
const first=await registrar(a.id,payload('same'))
const repeated=await Promise.all(Array.from({length:20},()=>registrar(a.id,payload('same'))))
assert(repeated.every(x=>x.id===first.id&&x.reutilizado))
assert.equal(Number((await db.query('select count(*) n from cti_feira_itens')).rows[0].n),1)
await assert.rejects(registrar(a.id,{...payload('same'),empresa:'Alterada'}),/conteúdo diferente/)
await assert.rejects(registrar(a.id,payload('broken'),[{...itens[0],quantidade:-1}]))
assert.equal(Number((await db.query("select count(*) n from cti_feira_atendimentos where client_request_id='broken'")).rows[0].n),0)
assert((await registrar(a.id,payload('broken'))).id)
await registrar(b.id,payload('same'))
assert.equal(Number((await db.query('select count(*) n from cti_feira_atendimentos where autorizada_id=$1',[uuid(3)])).rows[0].n),1)
await db.query('update cti_feira_autorizadas set ativa=false where id=$1',[uuid(2)])
await assert.rejects(registrar(a.id,payload('revoked')),/revogados/)
await assert.rejects(provision(99,uuid(2)),/inativa/)
await db.query('update cti_feira_autorizadas set ativa=true where id=$1',[uuid(2)])
await db.query('update cti_user_permissions set feiras_eventos=false where user_id=$1',[a2.id])
await assert.rejects(registrar(a2.id,payload('permission-revoked')),/revogados/)
for(const role of ['anon','authenticated']){
 await db.exec('set role '+role)
 await assert.rejects(db.query('select * from cti_feira_atendimentos'),/permission denied/)
 await assert.rejects(registrar(b.id,payload('bypass')),/permission denied/)
 await db.exec('reset role')
}
const loads=[]
for(const concurrency of [1,10,50]){
 const start=performance.now();const times=[]
 await Promise.all(Array.from({length:concurrency},async(_,i)=>{const t=performance.now();await registrar(b.id,payload(`load-${concurrency}-${i}`));times.push(performance.now()-t)}))
 times.sort((x,y)=>x-y);loads.push({concurrency,requests:concurrency,errors:0,elapsedMs:Math.round(performance.now()-start),p95Ms:Math.round(times[Math.ceil(times.length*.95)-1])})
}
const report={environment:'PostgreSQL WASM PGlite isolated, synthetic data; not Render/Supabase capacity',checks:['migration reapplication','professional provisioning','manager provisioning','forced least privilege','idempotent replay x20','payload conflict','item failure atomic rollback','recovery after failure','per-company ownership','company revocation','permission revocation','inactive company provisioning rejected','anon direct table denied','authenticated direct table denied','public RPC denied'],loads}
writeFileSync(new URL('./database-results.json',import.meta.url),JSON.stringify(report,null,2))
console.log(JSON.stringify(report,null,2));await db.close()
