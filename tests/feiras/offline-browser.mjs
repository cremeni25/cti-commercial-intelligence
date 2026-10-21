import {chromium} from '@playwright/test'
import {createServer,request} from 'node:http'
import {spawn} from 'node:child_process'
import {writeFileSync,mkdtempSync,rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
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
const profileDir=mkdtempSync(join(tmpdir(),'cti-offline-restart-'))
const launch=()=>chromium.launchPersistentContext(profileDir,{headless:true,executablePath:process.env.CTI_CHROMIUM_EXECUTABLE,args:['--no-sandbox','--disable-dev-shm-usage'],viewport:{width:390,height:844},serviceWorkers:'allow'})
let context=await launch()
const checks=[]
try{
 let page=await context.newPage()
 await context.addInitScript(perfil=>{if(!localStorage.getItem('cti-offline-fixture-initialized')){sessionStorage.setItem('cti-auth-session-v1',JSON.stringify({access_token:'synthetic-offline-test-token',refresh_token:'synthetic',expires_at:Math.floor(Date.now()/1000)+3600,user:{id:perfil.auth_id,email:perfil.email}}));localStorage.setItem('cti-offline-fixture-initialized','true')}},perfil)
 page.on('console',m=>{if(m.type()==='error')console.error(m.text())})
 await page.goto(origin+'/crm-app/feiras')
 await page.getByRole('heading',{name:'Feiras e Eventos',exact:true}).waitFor()
 assert.equal(await page.getByLabel('Senha exclusiva do cofre').count(),0)
 await page.getByLabel('Empresa *',{exact:true}).waitFor()
 checks.push('CTI authenticated online module does not require a separate password')
 await context.setOffline(true)
 await page.evaluate(()=>window.dispatchEvent(new Event('offline')))
 await page.getByLabel('Empresa *',{exact:true}).waitFor({state:'hidden'})
 checks.push('offline form unavailable without insecure storage or secondary password')
 await context.setOffline(false)
 await page.evaluate(()=>window.dispatchEvent(new Event('online')))
 await page.getByLabel('Empresa *',{exact:true}).waitFor({state:'visible'})
 checks.push('online form resumes after reconnection')
 const report={environment:'Chromium, local Next.js production build, synthetic CTI account and local API server; offline creation intentionally disabled',checks}
 writeFileSync(new URL('./offline-results.json',import.meta.url),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2))
}finally{await context.close();server.close();next.kill();rmSync(profileDir,{recursive:true,force:true})}
