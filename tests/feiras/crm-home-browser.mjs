import { chromium } from '@playwright/test'
import { writeFileSync } from 'node:fs'
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'

const next = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--port', '3103', '--hostname', '127.0.0.1'], {
  cwd: new URL('../../frontend/', import.meta.url),
  env: { ...process.env, NEXT_PUBLIC_SUPABASE_URL: 'https://example.supabase.co', NEXT_PUBLIC_SUPABASE_ANON_KEY: 'isolated-test-key' },
})
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(Error('Next did not start')), 15000)
  next.stdout.on('data', data => { if (String(data).includes('Ready')) { clearTimeout(timer); resolve() } })
  next.on('exit', code => reject(Error('Next exit ' + code)))
})
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] })
const checks = []
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, timezoneId: 'America/Sao_Paulo', serviceWorkers: 'block' })
  const perfil = { id: 'master', auth_id: 'test-auth', nome: 'Revisão CTI', email: 'test@example.invalid', tipo_usuario: 'ADMIN_MASTER', ativo: true, cadastro_completo: true, primeiro_acesso_pendente: false, acesso_crm: true, acesso_portal: false, permissoes: { financeiro_visualizar: true } }
  await context.addInitScript(perfil => sessionStorage.setItem('cti-auth-session-v1', JSON.stringify({ access_token: 'synthetic-only', refresh_token: 'synthetic', expires_at: 1893456000, user: { id: perfil.auth_id, email: perfil.email } })), perfil)
  let falharAtividades = true
  let consultas = 0
  await context.route('**/*', async route => {
    const url = new URL(route.request().url())
    if (url.hostname !== '127.0.0.1') return route.abort()
    if (!url.pathname.startsWith('/api/')) return route.continue()
    const json = (obj, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(obj) })
    if (url.pathname.startsWith('/api/crm-proxy/') && !route.request().headers().authorization) return json({detail: 'Authentication required'}, 401)
    if (url.pathname.endsWith('/clientes')) return json([{id:'account-a',nome:'Cliente isolado',cnpj:'11111111000111'},{id:'account-b',nome:'Cliente isolado',cnpj:'22222222000122'}])
    if (url.pathname === '/api/cti/auth/me') return json(perfil)
    if (url.pathname.endsWith('/nucleo-comercial')) {
      consultas += 1
      await new Promise(resolve => setTimeout(resolve, 150))
      return json([{ id: 'deal-1', cliente_id: 'account-b', cliente_nome: 'Cliente isolado', titulo: 'Proposta em andamento', etapa: 'PROPOSTA', responsavel_id: 'master' }])
    }
    if (url.pathname.endsWith('/atividades')) return falharAtividades ? json({ detail: 'Fonte temporariamente indisponível' }, 500) : json([{ id: 'visit-1', tipo: 'VISITA', data: '2026-10-25', usuario_id: 'master' }])
    return json([])
  })
  const page = await context.newPage()
  await page.clock.setFixedTime(new Date('2026-10-26T01:30:00Z'))
  page.on('pageerror', error => console.error('PAGE', error.message))
  await page.goto('http://127.0.0.1:3103/crm-app')
  await page.getByText('Não foi possível sincronizar o CRM agora.', { exact: true }).waitFor({timeout: 15000}).catch(async error => { console.error(await page.locator('body').innerText()); throw error })
  const visits = page.locator('a[href="/crm-app/visitas"] strong')
  assert.equal(await visits.textContent(), '—')
  assert.equal(await page.locator('a[href="/crm-app/oportunidades"] strong').first().textContent(), '1')
  checks.push('falha parcial não vira zero e preserva indicadores confirmados')
  const antes = consultas
  falharAtividades = false
  await page.getByLabel('Sincronizar CRM').evaluate(button => { button.click(); button.click() })
  await page.waitForFunction(() => document.querySelector('a[href="/crm-app/visitas"] strong')?.textContent === '1')
  assert.equal(consultas, antes + 1)
  checks.push('cliques simultâneos não duplicam a sincronização')
  checks.push('visita de hoje permanece no dia brasileiro depois de 21h')
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
  checks.push('tela inicial sem rolagem horizontal em 390px')
  await page.goto('http://127.0.0.1:3103/crm-app/acao')
  await page.getByRole('heading', { name: 'O que você quer fazer agora?' }).waitFor()
  assert.equal(await page.locator('a[href="/crm-app/acao/negociacao"]').count(), 1)
  checks.push('negociação e proposta compartilham uma única entrada')
  await page.goto('http://127.0.0.1:3103/crm-app/clientes')
  await page.getByText('2 clientes cadastrados', {exact: true}).waitFor()
  await page.getByPlaceholder('Buscar por nome, razão social, fantasia ou CNPJ').fill('Cliente isolado')
  assert.equal(await page.locator('a[href^="/crm-app/clientes/account-"]').count(), 2)
  assert.match(await page.locator('a[href^="/crm-app/clientes/account-a"]').innerText(), /0 negociações/)
  assert.match(await page.locator('a[href^="/crm-app/clientes/account-b"]').innerText(), /1 negociação/)
  checks.push('carteira autentica as duas fontes e preserva homônimos com negócios por ID')
  perfil.tipo_usuario = 'USUARIO_CTI'
  perfil.permissoes = { oportunidades_visualizar: true }
  await page.goto('http://127.0.0.1:3103/crm-app')
  await page.reload()
  await page.getByRole('heading', { name: 'Meu dia', exact: true }).waitFor()
  assert.equal(await page.locator('a[href="/crm-app/feiras"]').count(), 0)
  assert.equal(await page.locator('a[href="/crm-app/propostas"]').count(), 0)
  assert.equal(await page.locator('a[href="/crm-app/pedidos"]').count(), 0)
  assert.equal(await page.locator('a[href="/crm-app/clientes"]').count(), 0)
  checks.push('atalhos respeitam permissões sem mudar a autorização do backend')
  await context.close()
  const report = { engine: 'Chromium real e Next build; APIs e identidades sintéticas, sem produção', checks }
  writeFileSync(new URL('./crm-home-results.json', import.meta.url), JSON.stringify(report, null, 2))
  console.log(JSON.stringify(report, null, 2))
} finally {
  await browser.close()
  next.kill('SIGTERM')
}
