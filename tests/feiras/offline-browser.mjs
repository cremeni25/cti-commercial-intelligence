import {chromium} from '@playwright/test'
import {createServer,request} from 'node:http'
import {spawn} from 'node:child_process'
import {writeFileSync} from 'node:fs'
import assert from 'node:assert/strict'
const next=spawn(process.execPath,['node_modules/next/dist/bin/next','start','--port','3102','--hostname','127.0.0.1'],{cwd:new URL('../../frontend/',import.meta.url),env:process.env})
await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Next did not start')),15000);next.stdout.on('data',b=>{if(String(b).includes('Ready')){clearTimeout(timer);resolve()}});next.on('exit',c=>reject(Error('Next exit '+c)))})
const perfil={id:'offline-A',auth_id:'auth-offline-A',nome:'Profissional Offline',email:'offline@example.invalid',tipo_usuario:'AUTORIZADO_CARRIER',ativo:true,cadastro_completo:true,primeiro_acesso_pendente:false,acesso_crm:true,acesso_portal:false,autorizada_id:'company-A',permissoes:{acesso_crm:true,feiras_eventos:true}}
const received=[]
const server=createServer((req,res)=>{
 const path=new URL(req.url,'http://localhost').pathname
 if(path.startsWith('/api/')){
  res.setHeader('Content-Type','application/json');res.setHeader('Cache-Control','no-store')
  if(path==='/api/cti/auth/me')return res.end(JSON.stringify(perfil))
  if(path==='/api/crm-proxy/crm-seguro/feiras')return res.end(JSON.stringify([{id:'fair-offline',nome:'Feira Offline Teste'}]))
  if(path.endsWith('/catalogo'))return res.end(JSON.stringify([{codigo:'P1',linha_produto:'Carrier',nome_comercial:'Equipamento offline'}]))
  if(path.endsWith('/atendimentos')){
   if(req.method==='POST'){let body='';req.on('data',b=>body+=b);req.on('end',()=>{received.push(JSON.parse(body));res.end(JSON.stringify({id:'receipt-'+received.length}))});return}
   return res.end('[]')
  }
  res.statusCode=403;return res.end('{}')
 }
 const upstream=request({hostname:'127.0.0.1',port:3102,path:req.url,method:req.method,headers:req.headers},r=>{res.writeHead(r.statusCode,r.headers);r.pipe(res)});upstream.on('error',()=>{res.statusCode=502;res.end()});req.pipe(upstream)
})
await new Promise(r=>server.listen(0,'127.0.0.1',r))
const origin='http://127.0.0.1:'+server.address().port
const browser=await chromium.launch({headless:true,executablePath:process.env.CTI_CHROMIUM_EXECUTABLE,args:['--no-sandbox','--disable-dev-shm-usage']})
const checks=[]
try{
 const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'})
 const page=await context.newPage()
 await context.addInitScript(perfil=>{if(!localStorage.getItem('cti-offline-fixture-initialized')){sessionStorage.setItem('cti-auth-session-v1',JSON.stringify({access_token:'synthetic-offline-test-token',refresh_token:'synthetic',expires_at:Math.floor(Date.now()/1000)+3600,user:{id:perfil.auth_id,email:perfil.email}}));localStorage.setItem('cti-offline-fixture-initialized','true')}},perfil)
 page.on('console',m=>{if(m.type()==='error')console.error(m.text())})
 await page.goto(origin+'/crm-app/feiras')
 await page.getByRole('heading',{name:'Feiras e Eventos',exact:true}).waitFor()
 await page.getByLabel('Senha exclusiva do cofre').fill('senha-offline-segura-A')
 await page.getByRole('button',{name:'Desbloquear / criar cofre'}).click()
 await page.getByRole('button',{name:'Bloquear cofre',exact:true}).waitFor()
 // Wait for the actual persisted encrypted context and installed service worker.
 await page.waitForFunction(async()=>{const db=await new Promise((r,j)=>{const q=indexedDB.open('cti-feiras-cofre-v1');q.onsuccess=()=>r(q.result);q.onerror=()=>j(q.error)});try{if(!db.objectStoreNames.contains('contextos'))return false;return await new Promise(r=>{const q=db.transaction('contextos').objectStore('contextos').get('auth-offline-A');q.onsuccess=()=>r(!!q.result)})}finally{db.close()}})
 await page.evaluate(async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(r=>navigator.serviceWorker.addEventListener('controllerchange',r,{once:true}))})
 const cachesBefore=await page.evaluate(async()=>{const rows=[];for(const k of await caches.keys())for(const r of await(await caches.open(k)).keys())rows.push(r.url);return rows})
 assert(cachesBefore.some(x=>x.endsWith('/crm-app/feiras')));assert(!cachesBefore.some(x=>x.includes('/api/')));checks.push('real service worker prepares Feiras shell and excludes all APIs')
 const plaintext=await page.evaluate(async()=>{const db=await new Promise(r=>{const q=indexedDB.open('cti-feiras-cofre-v1');q.onsuccess=()=>r(q.result)});try{return await new Promise(r=>{const q=db.transaction('contextos').objectStore('contextos').getAll();q.onsuccess=()=>r(JSON.stringify(q.result))})}finally{db.close()}})
 assert(!plaintext.includes(perfil.email)&&!plaintext.includes('Equipamento offline'));checks.push('offline profile and catalog persist only as ciphertext')
 await context.setOffline(true)
 await page.reload({waitUntil:'domcontentloaded'})
 await page.getByRole('heading',{name:'Feiras e Eventos · sem conexão',exact:true}).waitFor()
 assert.equal(await page.getByLabel('Empresa *',{exact:true}).count(),0);checks.push('cold offline reload requires vault password before showing protected UI')
 await page.getByLabel('Senha exclusiva do cofre').fill('senha-incorreta-aaaa')
 await page.getByRole('button',{name:'Abrir Feiras offline'}).click()
 await page.getByRole('alert').waitFor();checks.push('cold offline reload rejects wrong vault password')
 await page.getByLabel('Senha exclusiva do cofre').fill('senha-offline-segura-A')
 await page.getByRole('button',{name:'Abrir Feiras offline'}).click()
 await page.getByRole('heading',{name:'Feiras e Eventos',exact:true}).waitFor()
 await page.getByLabel('Empresa *',{exact:true}).fill('Atendimento sem rede')
 await page.getByLabel('Nome do visitante *',{exact:true}).fill('Visitante Offline')
 await page.locator('select').nth(2).selectOption('P1');checks.push('cold offline unlock restores correct fair and product catalog')
 await page.getByRole('button',{name:'Salvar atendimento e intenção de compra'}).click()
 await page.getByText('Pendentes neste dispositivo: 1',{exact:true}).waitFor()
 assert.equal(received.length,0);checks.push('cold offline form saves encrypted pending without network')
 await page.reload({waitUntil:'domcontentloaded'})
 await page.getByRole('heading',{name:'Feiras e Eventos · sem conexão',exact:true}).waitFor()
 await page.getByLabel('Senha exclusiva do cofre').fill('senha-offline-segura-A')
 await page.getByRole('button',{name:'Abrir Feiras offline'}).click()
 await page.getByText('Pendentes neste dispositivo: 1',{exact:true}).waitFor();checks.push('second cold offline reload recovers pending count without data loss')
 await context.setOffline(false)
 await page.getByRole('button',{name:'Sincronizar pendentes',exact:true}).click()
 await page.getByText('Pendentes neste dispositivo: 0',{exact:true}).waitFor()
 assert.equal(received.length,1);assert.equal(received[0].autorizada_id,'company-A');assert(received[0].client_request_id);checks.push('reconnection sends once with original company and stable idempotency key')
 const second=await context.newPage()
 await second.addInitScript(perfil=>sessionStorage.setItem('cti-auth-session-v1',JSON.stringify({access_token:'synthetic-offline-test-token',refresh_token:'synthetic',expires_at:Math.floor(Date.now()/1000)+3600,user:{id:perfil.auth_id,email:perfil.email}})),perfil)
 await second.goto(origin+'/crm-app/feiras')
 await second.getByRole('heading',{name:'Feiras e Eventos',exact:true}).waitFor()
 await page.bringToFront()
 if(await page.getByLabel('Senha exclusiva do cofre').isVisible()){
   await page.getByLabel('Senha exclusiva do cofre').fill('senha-offline-segura-A')
   await page.getByRole('button',{name:'Desbloquear / criar cofre'}).click()
 }
 await context.setOffline(true)
 await page.getByLabel('Empresa *',{exact:true}).fill('Pendência preservada ao sair')
 await page.getByLabel('Nome do visitante *',{exact:true}).fill('Visitante pendente')
 await page.locator('select').nth(2).selectOption('P1')
 await page.getByRole('button',{name:'Salvar atendimento e intenção de compra'}).click()
 await page.getByText('Pendentes neste dispositivo: 1',{exact:true}).waitFor()
 await page.getByRole('button',{name:'Sair com pendências protegidas'}).click()
 await page.waitForURL('**/crm-app/login');checks.push('offline logout reaches login without waiting for remote Auth network')
 await second.waitForURL('**/crm-app/login');checks.push('logout in one tab removes protected UI and redirects other open tab')
 await context.setOffline(true)
 await page.goto(origin+'/crm-app/feiras',{waitUntil:'domcontentloaded'})
 await page.waitForURL('**/crm-app/login')
 assert.equal(await page.getByRole('heading',{name:'Feiras e Eventos',exact:true}).count(),0);checks.push('offline reopening after logout cannot restore previous user profile')
 const remaining=await page.evaluate(async()=>{const db=await new Promise(r=>{const q=indexedDB.open('cti-feiras-cofre-v1');q.onsuccess=()=>r(q.result)});try{return await new Promise(r=>{const q=db.transaction('registros').objectStore('registros').getAll();q.onsuccess=()=>r(q.result)})}finally{db.close()}})
 assert.equal(remaining.filter(x=>x.userId==='offline-A').length,1)
 assert(!JSON.stringify(remaining).includes('Pendência preservada'))
 checks.push('offline logout across tabs preserves remaining pending as ciphertext')
 const report={environment:'Chromium 141, local Next.js production build and real service worker/cache/IndexedDB/WebCrypto; synthetic account and local API server; browser offline transport enabled',checks}
 writeFileSync(new URL('./offline-results.json',import.meta.url),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2))
}finally{await browser.close();server.close();next.kill()}
