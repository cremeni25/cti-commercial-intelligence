// Central de Inteligência e Prioridades do app: Chromium real, build Next real,
// APIs e identidades sintéticas. Nenhum dado de produção é acessado.
import { chromium } from '@playwright/test'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'

const PORTA = 3104
const BASE = `http://127.0.0.1:${PORTA}`
const capturas = process.env.CTI_CAPTURAS_DIR || ''
if (capturas) mkdirSync(capturas, { recursive: true })

const next = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--port', String(PORTA), '--hostname', '127.0.0.1'], {
  cwd: new URL('../../frontend/', import.meta.url),
  env: { ...process.env, NEXT_PUBLIC_SUPABASE_URL: 'https://example.supabase.co', NEXT_PUBLIC_SUPABASE_ANON_KEY: 'isolated-test-key' },
})
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(Error('Next did not start')), 20000)
  next.stdout.on('data', data => { if (String(data).includes('Ready')) { clearTimeout(timer); resolve() } })
  next.on('exit', code => reject(Error('Next exit ' + code)))
})

const prioridade = (id, extra) => ({
  codigo: 'PROPOSTA_SEM_RETORNO', categoria: 'risco', severidade: 'alta', titulo: `Proposta sem retorno há 12 dias: Frigorífico ${id}`,
  explicacao: 'Proposta P-12 enviada e sem nenhum movimento registrado desde 26/10/2026.', acao_recomendada: 'Ligue para o decisor e registre o retorno.',
  entidade_tipo: 'oportunidade', entidade_id: id, cliente_nome: `Frigorífico ${id}`, cliente_id: `cli-${id}`, responsavel_id: 'vend-1', valor: 480000, dias: 12,
  rota: `/oportunidades/${id}`, rota_app: `/crm-app/oportunidades/${id}`, evidencias: ['status_proposta=ENVIADA'], pontuacao: 120, sinais_relacionados: ['SEM_PROXIMO_PASSO'], ...extra,
})
const briefing = {
  versao: '1.0', gerado_em: '2026-11-07T01:30:00+00:00', data_referencia: '2026-11-06', escopo: { tipo: 'individual', responsavel_id: 'vend-1' },
  manchete: 'Você tem 2 follow-ups atrasados e R$ 1,2 mi em negócios que pedem atenção. Comece por Frigorífico Alfa.',
  indicadores: [
    { codigo: 'PIPELINE_ABERTO', rotulo: 'Pipeline aberto', valor: 2350000, formato: 'moeda', detalhe: '9 negócios', tom: 'neutro', rota: '/pipeline', rota_app: '/crm-app/pipeline' },
    { codigo: 'ACOES_HOJE', rotulo: 'Ações para hoje', valor: 3, formato: 'numero', detalhe: '2 atrasadas · 1 agendada', tom: 'atencao', rota: '/atividades', rota_app: '/crm-app/atividades' },
    { codigo: 'VALOR_EM_RISCO', rotulo: 'Valor em risco', valor: 1200000, formato: 'moeda', detalhe: 'Parados, vencidos ou sem retorno', tom: 'atencao', rota: '/oportunidades', rota_app: '/crm-app/oportunidades' },
    { codigo: 'PRONTOS_FECHAR', rotulo: 'Prontos para fechar', valor: 1, formato: 'numero', detalhe: 'Alta chance', tom: 'positivo', rota: '/forecast', rota_app: '/crm-app/forecast' },
    { codigo: 'GANHOS_MES', rotulo: 'Ganhos no mês', valor: 310000, formato: 'moeda', detalhe: '1 negócio fechado', tom: 'positivo', rota: '/vendas', rota_app: '/crm-app/vendas' },
  ],
  prioridades: [
    prioridade('Alfa'),
    prioridade('Beta', { codigo: 'PEDIDO_SEM_MOVIMENTO', titulo: 'Pedido sem movimento há 20 dias: Frigorífico Beta', entidade_tipo: 'pedido', entidade_id: 'ped-9', rota: '/pedidos/ped-9', rota_app: '/crm-app/pedidos/ped-9', sinais_relacionados: [] }),
    prioridade('Gama', { codigo: 'PRONTO_PARA_FECHAR', categoria: 'oportunidade', titulo: 'Pronto para fechar: Frigorífico Gama (80%)', sinais_relacionados: [] }),
    prioridade('Delta', { codigo: 'FOLLOWUP_ATRASADO', categoria: 'acao', severidade: 'media', titulo: 'Follow-up atrasado há 3 dias: Frigorífico Delta', entidade_tipo: 'atividade', rota: '/atividades', rota_app: '/crm-app/atividades', valor: 0, sinais_relacionados: [] }),
  ],
  riscos: [{ codigo: 'PROPOSTA_SEM_RETORNO', rotulo: 'Propostas sem retorno', quantidade: 2, valor: 960000 }],
  pipeline: { quantidade_aberta: 9, valor_aberto: 2350000, valor_ponderado: 990000, etapas: [
    { etapa: 'ATIVIDADE', rotulo: 'Em contato', quantidade: 4, valor: 800000, valor_ponderado: 240000 },
    { etapa: 'PROPOSTA', rotulo: 'Proposta', quantidade: 4, valor: 1300000, valor_ponderado: 650000 },
    { etapa: 'PEDIDO', rotulo: 'Pedido', quantidade: 1, valor: 250000, valor_ponderado: 250000 },
  ] },
  qualidade: { indice: 78, negocios_avaliados: 8, problemas: [{ codigo: 'SEM_PREVISAO', rotulo: 'Negócios sem previsão de fechamento', quantidade: 3, impacto: 'Não entram no planejamento do mês.', exemplos: [{ oportunidade_id: 'Alfa', cliente_nome: 'Frigorífico Alfa', rota: '/oportunidades/Alfa', rota_app: '/crm-app/oportunidades/Alfa' }] }] },
  sinais_por_codigo: { PROPOSTA_SEM_RETORNO: 2 }, total_sinais: 11, provedores: [], fontes: ['Núcleo comercial', 'Atividades e agenda'], limitacoes: [],
}
const modulos = [
  { codigo: 'oportunidades', nome: 'Oportunidades e pipeline', descricao: 'Negócios em andamento.', categoria: 'operacao', categoria_rotulo: 'Operação comercial', status: 'ativo', rota_web: '/oportunidades', rota_app: '/crm-app/oportunidades', consultado_pela_ia: true },
  { codigo: 'treinamentos', nome: 'Treinamentos comerciais', descricao: 'Trilhas por produto.', categoria: 'conhecimento', categoria_rotulo: 'Conhecimento', status: 'planejado', rota_web: null, rota_app: null, consultado_pela_ia: false },
]

const tabelaAplicacao = JSON.parse(readFileSync(new URL('../../backend/data/tabela_aplicacao.json', import.meta.url), 'utf8'))
const vitrine = {
  tabela_aplicacao: tabelaAplicacao,
  materiais_internos: [{ titulo: 'Tabela de aplicação (PDF)', url: 'https://exemplo.com/assinado/tabela.pdf', tipo: 'catalogo' }],
  fonte: 'catalogo_comercial', precos_visiveis: false, linktree_url: 'https://linktr.ee/exemplo-cti', total_equipamentos: 2,
  materiais_gerais: [{ titulo: 'Catálogo geral 2026', url: 'https://exemplo.com/geral.pdf', tipo: 'catalogo' }],
  linhas: [
    { codigo: 'TRAILER', nome: 'Trailer', sigla: 'TR', descricao: 'Semirreboques', materiais: [], equipamentos: [{ codigo: 'VECTOR-8500', nome_comercial: 'VECTOR 8500', modelo_base: 'VECTOR 8500', configuracao: 'PADRAO', compressor: null, possui_eletrico: false, descricao_tecnica: {}, preco_vigente: null, materiais: [{ titulo: 'Ficha Vector', url: 'https://exemplo.com/vector.pdf', tipo: 'ficha_tecnica' }] }] },
    { codigo: 'DIESEL TRUCK', nome: 'Diesel Truck', sigla: 'DT', descricao: 'Caminhões', materiais: [], equipamentos: [{ codigo: 'SUPRA-850', nome_comercial: 'SUPRA 850', modelo_base: 'SUPRA 850', configuracao: 'PADRAO', compressor: '05K 4CC', possui_eletrico: true, descricao_tecnica: {}, preco_vigente: null, materiais: [] }] },
    { codigo: 'DIRECT DRIVE', nome: 'Direct Drive', sigla: 'DD', descricao: 'Leves', materiais: [], equipamentos: [] },
  ],
}
let browser
const checks = []
async function contexto(perfil, viewport, cenario) {
  const ctx = await browser.newContext({ viewport, permissions: ['clipboard-read', 'clipboard-write'], timezoneId: 'America/Sao_Paulo', serviceWorkers: 'block', deviceScaleFactor: capturas ? 2 : 1 })
  await ctx.addInitScript(p => sessionStorage.setItem('cti-auth-session-v1', JSON.stringify({ access_token: 'synthetic-only', refresh_token: 'synthetic', expires_at: 1893456000, user: { id: p.auth_id, email: p.email } })), perfil)
  await ctx.route('**/*', async route => {
    const url = new URL(route.request().url())
    if (url.hostname !== '127.0.0.1') return route.abort()
    if (!url.pathname.startsWith('/api/')) return route.continue()
    const json = (obj, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(obj) })
    if (url.pathname.startsWith('/api/crm-proxy/') && !route.request().headers().authorization) return json({ detail: 'Authentication required' }, 401)
    if (url.pathname === '/api/cti/auth/me') return json(perfil)
    if (url.pathname.endsWith('/inteligencia/briefing')) {
      cenario.consultas.push(url.search)
      return cenario.briefing === 'legado' ? json([]) : cenario.briefing === 'ausente' ? json({ detail: 'Not Found' }, 404) : json(briefing)
    }
    if (url.pathname.endsWith('/plataforma/modulos')) return json({ modulos })
    if (url.pathname.endsWith('/notificacoes/config')) return json({ disponivel: cenario.push !== 'servidor_inativo', chave_publica: cenario.push === 'servidor_inativo' ? null : 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U' })
    const metodo = route.request().method()
    if (metodo !== 'GET') {
      const corpo = route.request().postData()
      ;(cenario.escritas ||= []).push({ metodo, caminho: url.pathname, corpo: corpo ? JSON.parse(corpo) : null })
      return json({ ok: true, suprimir_ate: '2026-12-06' }, url.pathname.endsWith('/inteligencia/feedback') ? 201 : 200)
    }
    if (url.pathname.endsWith('/catalogo/vitrine')) return json(vitrine)
    if (url.pathname.endsWith('/nucleo-comercial')) return json([{ id: 'deal-1', cliente_nome: 'Cliente isolado', titulo: 'Proposta', etapa: 'PROPOSTA', responsavel_id: perfil.id }])
    return json([])
  })
  return ctx
}
const vendedor = { id: 'vend-1', auth_id: 'auth-v', nome: 'Vendedora Teste', email: 'v@example.invalid', tipo_usuario: 'REPRES_REGIAO_01', ativo: true, cadastro_completo: true, primeiro_acesso_pendente: false, acesso_crm: true, acesso_portal: true, permissoes: { oportunidades_visualizar: true } }
const master = { ...vendedor, id: 'master', auth_id: 'auth-m', nome: 'Gestão Teste', tipo_usuario: 'ADMIN_MASTER', permissoes: {} }

try {
  browser = await chromium.launch({ headless: true, executablePath: process.env.CTI_CHROMIUM_PATH || undefined, args: ['--no-sandbox', '--disable-dev-shm-usage'] })
  // 1. App: card do agente na tela inicial
  let cenario = { briefing: 'ok', consultas: [] }
  let ctx = await contexto(vendedor, { width: 390, height: 844 }, cenario)
  let page = await ctx.newPage()
  page.on('pageerror', erro => { throw erro })
  await page.goto(`${BASE}/crm-app`)
  const comece = page.getByRole('region', { name: 'Comece por aqui' })
  await comece.getByText('Proposta sem retorno há 12 dias: Frigorífico Alfa').waitFor({ timeout: 15000 })
  assert.equal(await comece.getByText(/Frigorífico (Beta|Gama|Delta)/).count(), 0, 'uma prioridade por vez')
  assert.equal(await page.getByText(briefing.manchete).count(), 0, 'sem parágrafo de manchete na tela inicial')
  assert.equal(await page.locator('a[href="/crm-app/oportunidades/Alfa"]').count(), 1)
  assert.equal(await page.locator('a[href^="/crm-app/pedidos/"]').count(), 0, 'perfil sem pedidos não recebe link de pedido')
  assert.equal(await page.getByRole('heading', { name: 'Meu dia', exact: true }).count(), 1)
  assert.equal(await page.getByText('Negociação em destaque', { exact: false }).count(), 0)
  assert.equal(await page.locator('nav a[href="/crm-app/catalogo"]').count(), 1, 'Catálogo na barra inferior')
  await comece.getByText('Ver todas (4)').waitFor()
  checks.push('tela inicial do app: uma prioridade por vez, sem manchete nem destaque redundante, Catálogo na barra inferior')
  await comece.getByRole('button', { name: 'Agendar próximo passo' }).click()
  await comece.getByRole('button', { name: 'Agendar', exact: true }).click()
  await comece.getByRole('status').filter({ hasText: 'Próximo passo agendado' }).waitFor()
  await comece.getByText('Pedido sem movimento há 20 dias: Frigorífico Beta').waitFor()
  checks.push('resolver a prioridade na tela inicial mostra a próxima na hora')
  if (capturas) await page.screenshot({ path: `${capturas}/app-inicio.png`, fullPage: true })

  // 2. App: tela completa de prioridades
  await page.goto(`${BASE}/crm-app/prioridades`)
  await page.getByRole('heading', { name: 'Prioridades do dia' }).waitFor()
  // Espera a lista carregar antes de contar: no CI a tela pode chegar antes dos dados.
  await page.getByRole('list', { name: 'Lista de prioridades' }).locator('li').nth(3).waitFor({ timeout: 15000 })
  assert.equal(await page.locator('ol > li').count(), 4)
  assert.equal(await page.getByText(briefing.manchete).count(), 0, 'app sem parágrafo do agente')
  await page.getByRole('tab', { name: /^Oportunidade/ }).click()
  assert.equal(await page.locator('ol > li').count(), 1)
  checks.push('filtro por categoria reduz a lista às oportunidades')
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
  checks.push('prioridades sem rolagem horizontal em 390px')
  await page.getByRole('tab', { name: /^Todas/ }).click()
  if (capturas) await page.screenshot({ path: `${capturas}/app-prioridades.png`, fullPage: true })

  // 2b. Resolver prioridades sem sair da lista
  const lista = page.getByRole('list', { name: 'Lista de prioridades' })
  const alfa = lista.locator('li').filter({ hasText: 'Frigorífico Alfa' })
  await alfa.getByRole('button', { name: 'Agendar próximo passo' }).click()
  await alfa.getByLabel('Tipo de contato').selectOption('VISITA')
  await alfa.getByRole('button', { name: 'Agendar', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Próximo passo agendado' }).waitFor()
  assert.equal(await lista.locator('li').filter({ hasText: 'Frigorífico Alfa' }).count(), 0)
  const agendamento = cenario.escritas.findLast(item => item.caminho.endsWith('/crm-seguro/atividades'))
  assert.equal(agendamento.corpo.cliente_id, 'cli-Alfa')
  assert.equal(agendamento.corpo.oportunidade_id, 'Alfa')
  assert.equal(agendamento.corpo.tipo, 'VISITA')
  checks.push('agendar próximo passo usa o endpoint seguro de atividades e tira o item da lista')
  await lista.locator('li').filter({ hasText: 'Frigorífico Delta' }).getByRole('button', { name: 'Concluir' }).click()
  await page.getByRole('status').filter({ hasText: 'Atividade concluída' }).waitFor()
  assert.ok(cenario.escritas.some(item => item.metodo === 'PUT' && item.caminho.endsWith('/atividades/Delta/concluir')))
  checks.push('follow-up atrasado é concluído direto da prioridade')
  const gama = lista.locator('li').filter({ hasText: 'Frigorífico Gama' })
  await gama.getByRole('button', { name: 'Não se aplica / adiar' }).click()
  await gama.getByLabel('Motivo').selectOption('ALERTA_CEDO_DEMAIS')
  await gama.getByRole('button', { name: 'Confirmar' }).click()
  await page.getByRole('status').filter({ hasText: 'Alerta dispensado' }).waitFor()
  const ajuste = cenario.escritas.find(item => item.caminho.endsWith('/inteligencia/feedback'))
  assert.deepEqual([ajuste.corpo.codigo, ajuste.corpo.entidade_id, ajuste.corpo.decisao, ajuste.corpo.motivo], ['PRONTO_PARA_FECHAR', 'Gama', 'NAO_SE_APLICA', 'ALERTA_CEDO_DEMAIS'])
  await page.waitForTimeout(900)
  assert.equal(await lista.locator('li').count(), 1, 'itens resolvidos continuam fora após a releitura')
  checks.push('"não se aplica" registra motivo para calibrar o agente e mantém a lista limpa após recarregar')

  // 2c. Catálogo no app
  await page.goto(`${BASE}/crm-app/catalogo`)
  await page.getByRole('heading', { name: 'Catálogo de produtos' }).waitFor()
  await page.locator('a[href="https://linktr.ee/exemplo-cti"]').waitFor()
  assert.equal(await page.locator('a[href="https://linktr.ee/exemplo-cti"]').count(), 1)
  assert.equal(await page.getByText('Preço de tabela').count(), 0, 'vendedor sem proposta não vê preço')
  const aplicacao = page.getByRole('region', { name: 'Tabela de aplicação' })
  await aplicacao.getByRole('radio', { name: /5,5m/ }).click()
  await aplicacao.getByRole('radio', { name: '-18 °C' }).click()
  const atendem = await aplicacao.getByRole('list', { name: 'Equipamentos que atendem' }).locator('strong.block.text-white').allTextContents()
  assert.deepEqual(atendem.sort(), ['CITIMAX 500', 'CITIMAX 600', 'CITIMAX 700', 'XARIOS 6'])
  await aplicacao.getByRole('radio', { name: /2,8m/ }).click()
  await aplicacao.getByRole('radio', { name: '-25 °C' }).click()
  await aplicacao.getByText('Nenhum equipamento da tabela atende').waitFor()
  await aplicacao.getByRole('radio', { name: /5,5m/ }).click()
  await aplicacao.getByRole('radio', { name: '-18 °C' }).click()
  await aplicacao.getByRole('button', { name: 'Copiar recomendação para WhatsApp' }).click()
  assert.match(await page.evaluate(() => navigator.clipboard.readText()), /Baú 5,5m \(21,3 m³\) a -18 °C/)
  assert.equal(await page.locator('a[href="https://exemplo.com/assinado/tabela.pdf"]').count(), 1, 'PDF interno disponível')
  assert.equal(await page.getByText('Anexar PDF interno (Master)').count(), 0, 'vendedor não anexa materiais')
  if (capturas) await aplicacao.screenshot({ path: `${capturas}/app-tabela-aplicacao.png` })
  checks.push('tabela de aplicação no app: baú 5,5m a -18 °C indica Citimax 500/600/700 e Xarios 6, sem opção para combinação impossível, recomendação copiável e PDF interno')
  await page.getByPlaceholder('Buscar modelo, linha ou compressor').fill('05k')
  assert.equal(await page.locator('article').count(), 1)
  await page.getByRole('button', { name: 'Copiar para WhatsApp' }).click()
  await page.getByRole('status').filter({ hasText: 'SUPRA 850 copiado' }).waitFor()
  const copiadoTexto = await page.evaluate(() => navigator.clipboard.readText())
  assert.match(copiadoTexto, /\*SUPRA 850\* — Carrier Transicold, linha Diesel Truck \(DT\)/)
  assert.match(copiadoTexto, /Compressor: 05K 4CC/)
  await page.getByPlaceholder('Buscar modelo, linha ou compressor').fill('')
  await page.getByRole('tab', { name: 'Trailer' }).click()
  assert.equal(await page.locator('a[href="https://exemplo.com/vector.pdf"]').count(), 1)
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
  checks.push('catálogo no app: Linktree, busca, filtro por linha, material por modelo e resumo pronto para WhatsApp em 390px')
  await page.getByRole('tab', { name: 'Todas' }).click()
  if (capturas) await page.screenshot({ path: `${capturas}/app-catalogo.png`, fullPage: true })
  await ctx.close()

  // 2d. Resumo diário no celular (serviço de push do aparelho simulado)
  cenario = { briefing: 'ok', consultas: [] }
  ctx = await contexto(vendedor, { width: 390, height: 844 }, cenario)
  await ctx.addInitScript(() => {
    let assinatura = null
    const falsa = { endpoint: 'https://push.exemplo/aparelho-1', toJSON: () => ({ endpoint: 'https://push.exemplo/aparelho-1', keys: { p256dh: 'chave-p256dh', auth: 'chave-auth' } }), unsubscribe: async () => { assinatura = null; return true } }
    const pushManager = {
      getSubscription: async () => assinatura,
      subscribe: async (opcoes) => { if (!(opcoes.applicationServerKey instanceof Uint8Array)) throw Error('chave inválida'); assinatura = falsa; return falsa },
    }
    // O harness bloqueia service workers: simula o registro do app em /crm-app.
    navigator.serviceWorker.getRegistration = async () => ({ scope: location.origin + '/crm-app', pushManager })
    Object.defineProperty(Notification, 'permission', { get: () => 'default', configurable: true })
    Notification.requestPermission = async () => 'granted'
  })
  page = await ctx.newPage()
  await page.goto(`${BASE}/crm-app/prioridades`)
  await page.getByRole('button', { name: 'Ativar resumo diário' }).click({ timeout: 20000 })
  await page.getByText('Ativado. Nos dias úteis').waitFor()
  const inscricao = cenario.escritas.find(item => item.caminho.endsWith('/notificacoes/assinatura'))
  assert.deepEqual(inscricao.corpo, { endpoint: 'https://push.exemplo/aparelho-1', keys: { p256dh: 'chave-p256dh', auth: 'chave-auth' } })
  await page.getByRole('button', { name: 'Enviar teste' }).click()
  await page.getByText('Notificação de teste enviada').waitFor()
  await page.getByRole('button', { name: 'Desativar' }).click()
  await page.getByRole('button', { name: 'Ativar resumo diário' }).waitFor()
  assert.ok(cenario.escritas.some(item => item.caminho.endsWith('/notificacoes/assinatura/remover')))
  checks.push('resumo diário: ativar inscreve o aparelho, teste e desativação funcionam')
  if (capturas) await page.screenshot({ path: `${capturas}/app-resumo-diario.png` })
  await ctx.close()

  cenario = { briefing: 'ok', consultas: [], push: 'servidor_inativo' }
  ctx = await contexto(vendedor, { width: 390, height: 844 }, cenario)
  page = await ctx.newPage()
  await page.goto(`${BASE}/crm-app/prioridades`)
  await page.getByText('sendo ativado no servidor').waitFor({ timeout: 20000 })
  assert.equal(await page.getByRole('button', { name: 'Ativar resumo diário' }).count(), 0)
  checks.push('sem chaves no servidor, o app explica e não oferece ativação')
  await ctx.close()

  // 3. Backend anterior ao agente: o app segue intacto e o card some
  for (const tipo of ['legado', 'ausente']) {
    cenario = { briefing: tipo, consultas: [] }
    ctx = await contexto(vendedor, { width: 390, height: 844 }, cenario)
    page = await ctx.newPage()
    const erros = []
    page.on('pageerror', erro => erros.push(erro.message))
    await page.goto(`${BASE}/crm-app`)
    await page.getByRole('heading', { name: 'Meu dia', exact: true }).waitFor({ timeout: 15000 })
    await page.waitForFunction(() => !document.querySelector('[aria-busy="true"]'), null, { timeout: 15000 })
    assert.equal(await page.getByText('Comece por aqui').count(), 0)
    assert.deepEqual(erros, [])
    await ctx.close()
  }
  checks.push('resposta fora do contrato ou 404 esconde o card sem erro e preserva a tela inicial')

  // 4. Portal: Central de Inteligência para a gestão
  cenario = { briefing: 'ok', consultas: [] }
  ctx = await contexto(master, { width: 1440, height: 1000 }, cenario)
  page = await ctx.newPage()
  page.on('pageerror', erro => { throw erro })
  await page.goto(`${BASE}/central`)
  await page.getByRole('heading', { name: 'Central de Inteligência', level: 1 }).waitFor({ timeout: 15000 })
  await page.getByText(briefing.manchete).waitFor()
  await page.getByText('Leitura do agente · 06/11/2026').waitFor()
  checks.push('data de referência exibida como data civil brasileira (sem recuo de fuso)')
  await page.getByText('Treinamentos comerciais').waitFor()
  assert.equal(await page.locator('a[href="/pedidos/ped-9"]').count(), 1, 'gestão abre o pedido')
  assert.equal(await page.locator('a[href="/central"]').count() >= 1, true, 'Central aparece no menu')
  checks.push('Central no portal: manchete, KPIs, prioridades, módulos e menu')
  if (capturas) await page.screenshot({ path: `${capturas}/portal-central.png`, fullPage: true })
  await ctx.close()

  const report = { engine: 'Chromium real e Next build; APIs e identidades sintéticas, sem produção', checks }
  writeFileSync(new URL('./central-results.json', import.meta.url), JSON.stringify(report, null, 2))
  console.log(JSON.stringify(report, null, 2))
} finally {
  await browser?.close()
  next.kill('SIGTERM')
}
