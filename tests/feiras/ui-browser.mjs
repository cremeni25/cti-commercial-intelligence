import {chromium} from 'playwright'
import {writeFileSync} from 'node:fs'
import assert from 'node:assert/strict'
import {spawn} from 'node:child_process'
const next=spawn(process.execPath,['node_modules/next/dist/bin/next','start','--port','3100','--hostname','127.0.0.1'],{cwd:new URL('../../frontend/',import.meta.url),env:{...process.env,NEXT_PUBLIC_SUPABASE_URL:'https://example.supabase.co',NEXT_PUBLIC_SUPABASE_ANON_KEY:'isolated-test-key'}})
await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Next did not start')),15000);next.stdout.on('data',b=>{if(String(b).includes('Ready')){clearTimeout(timer);resolve()}});next.on('exit',code=>reject(Error('Next exit '+code)))})
const browser=await chromium.launch({headless:true,executablePath:process.env.CTI_CHROMIUM_EXECUTABLE,args:['--no-sandbox','--disable-dev-shm-usage']})
const checks=[]
try{
 const context=await browser.newContext({viewport:{width:390,height:844}})
 const perfil={id:'external-A',auth_id:'auth-A',nome:'Profissional Teste',email:'teste@example.invalid',tipo_usuario:'AUTORIZADO_CARRIER',ativo:true,cadastro_completo:true,primeiro_acesso_pendente:false,acesso_crm:true,acesso_portal:false,permissoes:{acesso_crm:true,feiras_eventos:true}}
 await context.addInitScript(({perfil})=>{sessionStorage.setItem('cti-auth-session-v1',JSON.stringify({access_token:'synthetic-local-test-token',refresh_token:'synthetic',expires_at:Math.floor(Date.now()/1000)+3600,user:{id:perfil.auth_id,email:perfil.email}}))},{perfil})
 let received=[];let edits=[];let networkFail=true;let editConflict=false;let rows=[]
 await context.route('**/*',async route=>{
   const u=new URL(route.request().url())
   if(u.hostname!=='127.0.0.1'){await route.abort();return}
   const path=u.pathname
   if(!path.startsWith('/api/')){await route.continue();return}
   const json=(obj,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(obj)})
   if(path==='/api/cti/auth/me')return json(perfil)
   if(path==='/api/crm-proxy/crm-seguro/feiras')return json([{id:'fair',nome:'Feira isolada'}])
   if(path.endsWith('/catalogo'))return json([{codigo:'P1',linha_produto:'Truck',nome_comercial:'Equipamento Teste'}])
   if(path.endsWith('/atendimentos/receipt-1')&&route.request().method()==='PUT'){
    const body=route.request().postDataJSON();edits.push(body)
    if(editConflict)return json({detail:'Conflito de versão simulado'},409)
    rows=[{...rows[0],...body,versao:1}];return json({id:'receipt-1',versao:1})
   }
   if(path.endsWith('/atendimentos')){
    if(route.request().method()==='POST'){
      if(networkFail)return json({detail:'Falha transitória simulada'},503)
      const body=route.request().postDataJSON();received.push(body);rows=[{...body,id:'receipt-1',criado_por:'external-A',versao:0,status:'REGISTRADO',criado_em:new Date().toISOString()}];return json({id:'receipt-1'},201)
    }
    return json(rows)
   }
   return json({detail:'Forbidden in isolated test'},403)
 })
 const page=await context.newPage();await page.goto('http://127.0.0.1:3100/crm-app/feiras')
 await page.getByRole('heading',{name:'Feiras e Eventos',exact:true}).waitFor()
 assert.equal(await page.getByRole('navigation',{name:'Navegação principal do CRM'}).count(),0);checks.push('external CRM navigation restricted')
 await page.getByLabel('Senha exclusiva do cofre').fill('senha-local-segura-A')
 await page.getByRole('button',{name:'Desbloquear / criar cofre'}).click()
 await page.getByRole('button',{name:'Bloquear cofre',exact:true}).waitFor()
 await page.getByLabel('Empresa *',{exact:true}).fill('Empresa Teste Offline')
 await page.getByLabel('Nome do visitante *',{exact:true}).fill('Visitante Teste')
 await page.locator('select').nth(2).selectOption('P1')
 await page.getByRole('button',{name:'Salvar atendimento e intenção de compra'}).click()
 await page.getByText('Pendentes neste dispositivo: 1',{exact:true}).waitFor()
 checks.push('UI saves encrypted queue before failed server response')
 assert.equal(await page.getByLabel('Empresa *',{exact:true}).inputValue(),'');checks.push('local save clears submitted form')
 networkFail=false
 await page.getByRole('button',{name:'Sincronizar pendentes',exact:true}).click()
 await page.getByText('Pendentes neste dispositivo: 0',{exact:true}).waitFor()
 assert.equal(received.length,1);assert(received[0].client_request_id);checks.push('UI reconnect sync includes stable idempotency key')
 await page.getByRole('button',{name:'Editar atendimento',exact:true}).click()
 await page.getByRole('button',{name:'Salvar edição protegida',exact:true}).waitFor()
 assert.equal(await page.getByLabel('Empresa *',{exact:true}).inputValue(),'Empresa Teste Offline');checks.push('edit reuses existing attendance form with original values')
 await page.getByLabel('Empresa *',{exact:true}).fill('Empresa Editada')
 editConflict=true
 await page.getByRole('button',{name:'Salvar edição protegida',exact:true}).click()
 await page.getByText('Pendentes neste dispositivo: 1',{exact:true}).waitFor()
 await page.getByRole('alert').filter({hasText:'Conflito de versão'}).waitFor()
 assert.equal(edits[0].versao_esperada,0);checks.push('edit sends expected version and preserves encrypted pending on conflict')
 editConflict=false
 await page.getByRole('button',{name:'Sincronizar pendentes',exact:true}).click()
 await page.getByText('Pendentes neste dispositivo: 0',{exact:true}).waitFor()
 assert.equal(edits[0].client_request_id,edits[1].client_request_id)
 await page.getByText('Empresa Editada',{exact:true}).waitFor();checks.push('edit retry uses same key and updates existing attendance without duplicate creation')
 assert.equal(received.length,1);assert.equal(rows.length,1)
 await page.getByRole('button',{name:'Bloquear cofre',exact:true}).click()
 assert.equal(await page.getByLabel('Empresa *',{exact:true}).isVisible(),false);checks.push('locked vault hides attendance form and data')
 await page.goto('http://127.0.0.1:3100/crm-app/oportunidades')
 await page.waitForURL('**/crm-app/feiras?acesso=restrito');checks.push('forbidden CRM URL redirects external user')
 writeFileSync(new URL('./ui-results.json',import.meta.url),JSON.stringify({environment:'Local Next.js production build; synthetic session and mocked API transport, mobile viewport 390x844',checks},null,2));console.log(JSON.stringify(checks,null,2))
}finally{await browser.close();next.kill()}
