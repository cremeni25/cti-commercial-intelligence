import { chromium } from '@playwright/test'
import ts from 'typescript'
import { readFileSync, writeFileSync } from 'node:fs'
import { createServer } from 'node:http'
const source = ts.transpileModule(readFileSync(new URL('../../frontend/src/core/auth/session.ts', import.meta.url), 'utf8').replace('import { getSupabaseClient } from "../database/supabase"', 'const getSupabaseClient = () => window.sdk').replaceAll('process.env.NEXT_PUBLIC_SUPABASE_URL', '"https://cti-test.supabase.co"'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } }).outputText
const server = createServer((req, res) => { res.setHeader('Cache-Control', 'no-store'); res.setHeader('Content-Type', req.url.startsWith('/session.js') ? 'text/javascript' : 'text/html'); res.end(req.url.startsWith('/session.js') ? source : '<!doctype html><title>CTI session isolation</title>') })
await new Promise(r => server.listen(0, '127.0.0.1', r))
const browser = await chromium.launch({ headless: true, executablePath: process.env.CTI_CHROMIUM_EXECUTABLE, args: ['--no-sandbox'] })
try {
 const context = await browser.newContext()
 const page = await context.newPage()
 await page.goto(`http://127.0.0.1:${server.address().port}`)
 const checks = await page.evaluate(async () => {
  const s = await import('/session.js'); const checks = []
  const check = (ok, name) => { if (!ok) throw Error(name); checks.push(name) }
  const session = id => ({ access_token: `token-${id}`, refresh_token: `refresh-${id}`, user: { id }, expires_at: Math.floor(Date.now()/1000)+3600 })
  const A=session('A'), B=session('B')
  window.sdk={auth:{getSession: async()=>({data:{session:null}})}}
  localStorage.setItem('sb-other-auth-token', JSON.stringify(A))
  check(await s.obterSessaoCTI() === null, 'unrelated Supabase project cannot supply CTI identity')
  s.iniciarSessaoCTI(A)
  localStorage.setItem('sb-cti-test-auth-token',JSON.stringify(A))
  sessionStorage.setItem('sb-cti-test-auth-token.0',JSON.stringify(A))
  s.registrarSessaoCTI(null)
  check(!localStorage.getItem('sb-cti-test-auth-token') && !sessionStorage.getItem('sb-cti-test-auth-token.0'), 'logout removes current-project persisted tokens')
  check(!!localStorage.getItem('sb-other-auth-token'), 'logout preserves unrelated project storage')
  check(await s.obterSessaoCTI() === null, 'offline logout immediately blocks session restoration')
  s.registrarSessaoCTI(A)
  check(await s.obterSessaoCTI() === null, 'late refresh cannot undo explicit logout')
  let denied=false;try{await s.obterTokenCTI()}catch{denied=true}
  check(denied,'API token unavailable after logout')
  s.iniciarSessaoCTI(B)
  check(await s.obterTokenCTI()==='token-B','explicit login enables only newly authenticated account')
  sessionStorage.removeItem('cti-auth-session-v1')
  // Obtain a fresh module with no memory cache and delay the SDK response across logout.
  const fresh=await import('/session.js?race')
  let finish;window.sdk.auth.getSession=()=>new Promise(r=>{finish=r})
  const pending=fresh.obterSessaoCTI()
  fresh.registrarSessaoCTI(null)
  finish({data:{session:A}})
  check(await pending===null && await fresh.obterSessaoCTI()===null,'in-flight session response cannot restore a logged-out identity')
  return checks
 })
 await page.reload()
 const persisted=await page.evaluate(async()=>{window.sdk={auth:{getSession:async()=>({data:{session:{access_token:'stale'}}})}};const s=await import('/session.js');return await s.obterSessaoCTI()===null})
 if(!persisted)throw Error('logout lost after reload')
 checks.push('reload preserves logout barrier even with stale SDK session')
 const report={engine:'real Chromium; synthetic SDK responses, real localStorage/sessionStorage',checks}
 writeFileSync(new URL('./session-results.json',import.meta.url),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2))
}finally{await browser.close();server.close()}
