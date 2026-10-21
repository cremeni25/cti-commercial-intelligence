import { chromium } from 'playwright'
import ts from 'typescript'
import {readFileSync,writeFileSync} from 'node:fs'
import {createServer} from 'node:http'
import assert from 'node:assert/strict'
const source=ts.transpileModule(readFileSync(new URL('../../frontend/src/lib/feiras-cofre.ts',import.meta.url),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText
const server=createServer((req,res)=>{res.setHeader('Cache-Control','no-store');if(req.url==='/vault.js'){res.setHeader('Content-Type','text/javascript');res.end(source)}else{res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>CTI isolated vault verification</title>')}})
await new Promise(r=>server.listen(0,'127.0.0.1',r))
const browser=await chromium.launch({headless:true,executablePath:process.env.CTI_CHROMIUM_EXECUTABLE,args:['--no-sandbox','--disable-dev-shm-usage']})
try{
 const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.address().port)
 const first=await page.evaluate(async()=>{
  const v=await import('/vault.js');window.v=v
  const results=[]
  const check=(condition,name)=>{if(!condition)throw Error(name);results.push(name)}
  const fails=async(fn,name)=>{try{await fn()}catch{results.push(name);return}throw Error(name+' did not reject')}
  await v.desbloquearCofre('A','senha-longa-segura-A')
  await v.salvarCifrado('A',{id:'same',feiraId:'fair',payload:{empresa:'Segredo pessoa A'}})
  check((await v.listarDecifrados('A'))[0].payload.empresa==='Segredo pessoa A','encrypted save and decrypt')
  const raw=await new Promise((resolve,reject)=>{const r=indexedDB.open('cti-feiras-cofre-v1');r.onsuccess=()=>{const db=r.result;const q=db.transaction('registros').objectStore('registros').getAll();q.onsuccess=()=>{resolve(q.result);db.close()};q.onerror=()=>reject(q.error)}})
  check(!JSON.stringify(raw).includes('Segredo pessoa'),'no plaintext in persistent queue')
  await fails(()=>v.sincronizarCofre('A',async()=>{throw Error('network timeout')}),'network failure keeps queue')
  check(await v.quantidadePendente('A')===1,'pending survives network failure')
  await fails(()=>v.sincronizarCofre('A',async()=>({})),'invalid acknowledgement keeps queue')
  v.bloquearCofre();await fails(()=>v.listarDecifrados('A'),'locked vault unreadable')
  await fails(()=>v.desbloquearCofre('A','senha-incorreta-aaaa'),'wrong password rejected')
  await v.desbloquearCofre('B','senha-longa-segura-B')
  await v.salvarCifrado('B',{id:'same',feiraId:'fair',payload:{empresa:'Segredo B'}})
  check(await v.quantidadePendente('A')===1&&await v.quantidadePendente('B')===1,'same record id isolated across accounts')
  await fails(()=>v.listarDecifrados('A'),'unlocking B does not unlock A')
  await v.confirmarSincronizacao('B','same')
  check(await v.quantidadePendente('A')===1,'acknowledging B preserves A')
  v.bloquearCofre();await fails(()=>v.desbloquearCofre('B','outra-senha-longa-B'),'password verifier survives empty queue')
  return results
 })
 await page.reload()
 const second=await page.evaluate(async()=>{
  const v=await import('/vault.js');const results=[]
  if(v.cofreDesbloqueado('A'))throw Error('Key persisted')
  results.push('reload discards unlock key')
  await v.desbloquearCofre('A','senha-longa-segura-A')
  if((await v.listarDecifrados('A')).length!==1)throw Error('lost data after reload')
  results.push('reload and unlock recover pending data')
  await v.sincronizarCofre('A',async()=>({id:'server-receipt'}))
  if(await v.quantidadePendente('A')!==0)throw Error('receipt did not remove pending')
  results.push('valid server receipt removes only acknowledged pending')
  await v.salvarCifrado('A',{id:'tamper',feiraId:'fair',payload:{empresa:'Test'}})
  await new Promise((resolve,reject)=>{const r=indexedDB.open('cti-feiras-cofre-v1');r.onsuccess=()=>{const db=r.result;const tx=db.transaction('registros','readwrite');const s=tx.objectStore('registros');const q=s.getAll();q.onsuccess=()=>{for(const item of q.result){item.ciphertext[0]^=1;s.put(item)}};tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>reject(tx.error)}})
  let rejected=false;try{await v.listarDecifrados('A')}catch{rejected=true}
  if(!rejected)throw Error('tamper accepted');results.push('AES-GCM rejects tampered ciphertext')
  if(await v.quantidadePendente('A')!==1)throw Error('tamper deleted pending');results.push('corrupt pending preserved for recovery')
  const unlock=v.desbloquearCofre('A','senha-longa-segura-A')
  v.bloquearCofre()
  let cancelled=false;try{await unlock}catch{cancelled=true}
  if(!cancelled||v.cofreDesbloqueado('A'))throw Error('late unlock restored key')
  results.push('logout cancels in-flight vault unlock without restoring key')
  return results
 })
 const contextChecks=await page.evaluate(async()=>{
  const v=await import('/vault.js'),checks=[]
  const check=(ok,name)=>{if(!ok)throw Error(name);checks.push(name)}
  const fails=async(fn,name)=>{try{await fn()}catch{checks.push(name);return}throw Error(name+' did not reject')}
  await v.desbloquearCofre('A','senha-longa-segura-A')
  const perfil={id:'A',auth_id:'auth-A',nome:'Nome secreto A',email:'pessoal@example.invalid',ativo:true}
  await v.salvarContextoFeiras({perfil,feiras:[{id:'fair',nome:'Feira confidencial'}],catalogo:[{codigo:'P1',nome_comercial:'Produto A'}],expiraEm:Date.now()+60000})
  check((await v.lerContextoFeiras('auth-A')).perfil.id==='A','encrypted offline context bound to profile and auth identity')
  v.bloquearCofre()
  await fails(()=>v.lerContextoFeiras('auth-A'),'locked offline context cannot reveal profile or catalog')
  await fails(()=>v.recuperarContextoFeiras('auth-unknown','senha-longa-segura-A'),'another Auth identity cannot discover or unlock A context')
  await v.desbloquearCofre('B','senha-longa-segura-B')
  await fails(()=>v.lerContextoFeiras('auth-A'),'unlocking B cannot decrypt offline context A')
  await v.recuperarContextoFeiras('auth-A','senha-longa-segura-A')
  check((await v.lerContextoFeiras('auth-A')).catalogo[0].codigo==='P1','matching identity and vault password restore offline catalog')
  await v.salvarContextoFeiras({perfil,feiras:[],catalogo:[],expiraEm:Date.now()+1000})
  const now=Date.now;Date.now=()=>now()+2000
  try{await fails(()=>v.lerContextoFeiras('auth-A'),'expired offline authorization rejected independently of pending records')}finally{Date.now=now}
  check(await v.quantidadePendente('A')===1,'expired offline context preserves encrypted pending for later recovery')
  return checks
 })
 const report={engine:'Chromium real Web Crypto + IndexedDB, isolated synthetic data',checks:[...first,...second,...contextChecks]};writeFileSync(new URL('./vault-results.json',import.meta.url),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2))
}finally{await browser.close();server.close()}
