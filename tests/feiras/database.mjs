import { PGlite } from '@electric-sql/pglite'
import { readFileSync,writeFileSync } from 'node:fs'
import assert from 'node:assert/strict'
const db=new PGlite()
await db.exec(`
create role anon;create role authenticated;create role service_role bypassrls;
create table cti_users (id uuid primary key default gen_random_uuid(),auth_id uuid,email text,nome text,empresa text,cargo text,funcao text,tipo_usuario text,territorio text,ddds text[],gestor_responsavel text,superior_id uuid,ativo boolean,status_acesso text,primeiro_acesso_pendente boolean,cadastro_completo boolean,senha_temporaria_criada_em timestamptz,created_at timestamptz,updated_at timestamptz);
create table cti_user_permissions (user_id uuid primary key references cti_users(id),acesso_portal boolean,acesso_crm boolean,acesso_total boolean,feiras_eventos boolean,updated_at timestamptz,created_at timestamptz);
create table cti_feiras(id uuid primary key,nome text);
create table cti_feira_atendimentos (id uuid primary key default gen_random_uuid(),feira_id uuid references cti_feiras(id),empresa text,cnpj text,visitante text,contato text,email text,cidade text,uf text,regiao text,autorizado_destino text,interesse text,observacoes text,moeda text,valor_referencia numeric,criado_por text,criado_em timestamptz default now(),status text default 'REGISTRADO',oportunidade_id uuid);
create table cti_feira_itens(id uuid primary key default gen_random_uuid(),atendimento_id uuid references cti_feira_atendimentos(id) on delete cascade,codigo_produto text,linha_produto text,nome_produto text,quantidade integer check(quantidade>0),lancamento_feira boolean,descricao_lancamento text);
`)
await db.exec(readFileSync(new URL('../../supabase/migrations/20261021101633_feiras_transacoes_isolamento.sql',import.meta.url),'utf8'))
// Reapplication must preserve schema and data.
await db.exec(readFileSync(new URL('../../supabase/migrations/20261021101633_feiras_transacoes_isolamento.sql',import.meta.url),'utf8'))
const editMigration=readFileSync(new URL('../../supabase/migrations/20261021144323_feiras_edicao_idempotente.sql',import.meta.url),'utf8')
await db.exec(editMigration);await db.exec(editMigration)
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
const editChecks=[]
const check=(ok,name)=>{assert(ok);editChecks.push(name)}
const edit=async(user,id,p,i=itens)=>(await db.query('select cti_feira_editar($1,$2,$3,$4) as r',[user,id,JSON.stringify(p),JSON.stringify(i)])).rows[0].r
const base=payload('edit-base'),editable=await registrar(a.id,base)
const editPayload={...payload('edit-1'),autorizada_id:uuid(2),empresa:'Empresa editada',versao_esperada:0}
const changed=await edit(a.id,editable.id,editPayload,[{...itens[0],quantidade:2}])
check(changed.versao===1,'edit atomically updates attendance and increments version')
const editedRows=await db.query('select empresa,versao,criado_por,autorizada_id,client_request_id from cti_feira_atendimentos where id=$1',[editable.id])
check(editedRows.rows[0].empresa==='Empresa editada'&&editedRows.rows[0].criado_por===a.id&&editedRows.rows[0].autorizada_id===uuid(2)&&editedRows.rows[0].client_request_id==='edit-base','edit preserves creator company and original creation key')
check((await db.query('select quantidade from cti_feira_itens where atendimento_id=$1',[editable.id])).rows[0].quantidade===2,'edit replaces items without duplicates')
const editReplay=await Promise.all(Array.from({length:10},()=>edit(a.id,editable.id,editPayload,[{...itens[0],quantidade:2}])))
check(editReplay.every(r=>r.id===editable.id&&r.versao===1&&r.reutilizado),'edit replay x10 returns original receipt without version bump')
await assert.rejects(edit(a.id,editable.id,{...editPayload,empresa:'Outro conteudo'}),/conteúdo diferente/);editChecks.push('edit key content conflict rejected')
await assert.rejects(edit(a.id,editable.id,{...editPayload,client_request_id:'stale'}),/outra operação/);editChecks.push('stale edit cannot overwrite newer version')
await assert.rejects(edit(b.id,editable.id,{...editPayload,autorizada_id:uuid(3)}),/não localizado/);editChecks.push('cross-company edit rejected')
await assert.rejects(edit(gestor.id,editable.id,editPayload),/não localizado/);editChecks.push('manager company visibility does not grant editing other professionals')
await assert.rejects(edit(a2.id,editable.id,editPayload),/revogados/);editChecks.push('revoked permission blocks edit')
await db.query('update cti_feira_profissionais set autorizada_id=$1 where user_id=$2',[uuid(3),a.id])
await assert.rejects(edit(a.id,editable.id,{...editPayload,autorizada_id:uuid(3)}),/não localizado/);editChecks.push('transferred professional cannot edit old-company record')
await db.query('update cti_feira_profissionais set autorizada_id=$1 where user_id=$2',[uuid(2),a.id])
const nextEdit={...editPayload,client_request_id:'edit-recovery',versao_esperada:1,empresa:'Recuperacao'}
await assert.rejects(edit(a.id,editable.id,nextEdit,[{...itens[0],quantidade:-1}]))
check((await db.query('select versao,empresa from cti_feira_atendimentos where id=$1',[editable.id])).rows[0].versao===1,'failed edit item rolls back parent version and data')
check((await edit(a.id,editable.id,nextEdit)).versao===2,'failed edit can retry successfully with same key')
check((await registrar(a.id,base)).id===editable.id,'lost original creation receipt replay never duplicates edited attendance')
await db.query("update cti_feira_atendimentos set oportunidade_id=$1,status='CONVERTIDO' where id=$2",[uuid(999),editable.id])
await assert.rejects(edit(a.id,editable.id,{...nextEdit,client_request_id:'converted',versao_esperada:2}),/convertido/);editChecks.push('new edit of converted attendance rejected')
check((await edit(a.id,editable.id,nextEdit)).reutilizado,'lost edit receipt recoverable after later conversion')
for(const role of ['anon','authenticated']){
 await db.exec('set role '+role)
 await assert.rejects(db.query('select * from cti_feira_edicoes'),/permission denied/)
 await assert.rejects(edit(a.id,editable.id,nextEdit),/permission denied/)
 await db.exec('reset role')
}
editChecks.push('edit receipt table and RPC inaccessible to anon and authenticated roles')
await db.exec('grant all on cti_users,cti_user_permissions to service_role; set role service_role')
const serviceRecord=await registrar(b.id,payload('service-role-create'))
check((await edit(b.id,serviceRecord.id,{...payload('service-role-edit'),autorizada_id:uuid(3),versao_esperada:0})).versao===1,'service_role can execute authorized create and edit with declared table grants')
await db.exec('reset role')
await db.query("insert into cti_users(id,tipo_usuario,ativo) values($1,'ADMIN_MASTER',true),($2,null,true)",[uuid(700),uuid(701)])
check((await edit(uuid(700),serviceRecord.id,{...payload('master-edit'),versao_esperada:1})).versao===2,'internal Master can edit across authors without changing ownership')
await assert.rejects(edit(uuid(701),serviceRecord.id,{...payload('unknown-profile'),versao_esperada:2}),/Sem permissão/)
editChecks.push('null or unknown profile cannot inherit global edit authority')
const loads=[]
for(const concurrency of [1,10,50]){
 const start=performance.now();const times=[]
 await Promise.all(Array.from({length:concurrency},async(_,i)=>{const t=performance.now();await registrar(b.id,payload(`load-${concurrency}-${i}`));times.push(performance.now()-t)}))
 times.sort((x,y)=>x-y);loads.push({concurrency,requests:concurrency,errors:0,elapsedMs:Math.round(performance.now()-start),p95Ms:Math.round(times[Math.ceil(times.length*.95)-1])})
}
const report={environment:'PostgreSQL WASM PGlite isolated, synthetic data; not Render/Supabase capacity',checks:['migration reapplication','professional provisioning','manager provisioning','forced least privilege','idempotent replay x20','payload conflict','item failure atomic rollback','recovery after failure','per-company ownership','company revocation','permission revocation','inactive company provisioning rejected','anon direct table denied','authenticated direct table denied','public RPC denied',...editChecks],loads}
writeFileSync(new URL('./database-results.json',import.meta.url),JSON.stringify(report,null,2))
console.log(JSON.stringify(report,null,2));await db.close()
