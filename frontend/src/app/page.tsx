import Link from "next/link"
import {
  ArrowRight,
  BrainCircuit,
  ChartNoAxesCombined,
  CheckCircle2,
  DatabaseZap,
  Gauge,
  Globe2,
  Layers3,
  LockKeyhole,
  MapPinned,
  Radar,
  Route,
  ShieldCheck,
  Sparkles,
  Target,
  UsersRound,
} from "lucide-react"

const pilares = [
  {
    icon: DatabaseZap,
    titulo: "Fonte única de verdade",
    texto: "O CTI organiza dados comerciais dispersos em uma leitura coerente, rastreável e acionável.",
  },
  {
    icon: MapPinned,
    titulo: "Inteligência territorial",
    texto: "Região, carteira, histórico, mercado e contexto passam a fazer parte da mesma decisão comercial.",
  },
  {
    icon: BrainCircuit,
    titulo: "Decisão assistida",
    texto: "Indicadores, projeções e IA ajudam a transformar informação em prioridade, recomendação e ação.",
  },
  {
    icon: ShieldCheck,
    titulo: "Governança por perfil",
    texto: "Cada usuário acessa o que precisa para operar, gerir e decidir, sem romper a governança do negócio.",
  },
]

const fluxo = [
  ["01", "Capturar", "Dados comerciais, históricos e operacionais entram em um núcleo estruturado."],
  ["02", "Contextualizar", "O sistema cruza cliente, território, oportunidade, histórico, meta e mercado."],
  ["03", "Interpretar", "Indicadores e inteligência transformam volume de dados em leitura objetiva."],
  ["04", "Priorizar", "O CTI aponta onde agir, o que acompanhar e quais sinais exigem atenção."],
  ["05", "Executar", "CRM App e CTI Web conectam decisão e operação em uma mesma lógica comercial."],
]

const capacidades = [
  "CRM operacional integrado",
  "Pipeline e oportunidades",
  "Propostas, pedidos e vendas",
  "Histórico comercial consolidado",
  "Forecast e metas",
  "Inteligência territorial",
  "Relatórios e indicadores",
  "IA comercial aplicada",
]

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#020817] text-white selection:bg-cyan-400/30">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-[-24rem] h-[54rem] w-[54rem] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute right-[-14rem] top-[30rem] h-[36rem] w-[36rem] rounded-full bg-emerald-500/8 blur-3xl" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/8 bg-[#020817]/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
          <Link href="/" className="group flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl border border-cyan-400/30 bg-cyan-400/10 text-sm font-black tracking-tight text-cyan-300 shadow-[0_0_30px_rgba(34,211,238,.08)]">CTI</div>
            <div>
              <div className="text-sm font-semibold tracking-[.16em] text-white">COMERCIAL INTELLIGENCE</div>
              <div className="text-[10px] uppercase tracking-[.22em] text-slate-500">Inteligência para decisão</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-7 text-sm text-slate-400 md:flex">
            <a href="#filosofia" className="transition hover:text-white">Filosofia</a>
            <a href="#como-funciona" className="transition hover:text-white">Como funciona</a>
            <a href="#plataforma" className="transition hover:text-white">Plataforma</a>
          </nav>

          <Link
            href="https://app.cti-intelligence.com/dashboard"
            className="inline-flex items-center gap-2 rounded-xl border border-cyan-300/30 bg-cyan-300 px-4 py-2.5 text-sm font-bold text-[#02111d] transition hover:-translate-y-0.5 hover:bg-cyan-200"
          >
            Acessar CTI Web <ArrowRight size={16} />
          </Link>
        </div>
      </header>

      <section className="relative mx-auto grid min-h-[84vh] max-w-7xl items-center gap-14 px-5 py-20 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:py-24">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/8 px-3 py-1.5 text-xs font-semibold uppercase tracking-[.18em] text-cyan-300">
            <Sparkles size={14} /> Plataforma de inteligência comercial
          </div>
          <h1 className="max-w-4xl text-5xl font-black leading-[1.02] tracking-[-.045em] text-white sm:text-6xl lg:text-7xl">
            Dados só criam valor quando <span className="bg-gradient-to-r from-cyan-300 via-sky-300 to-emerald-300 bg-clip-text text-transparent">mudam a decisão.</span>
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-400 sm:text-xl">
            O CTI transforma dados comerciais, históricos, territoriais e operacionais em contexto, prioridade, previsão e ação. Não é apenas um CRM. É uma camada de inteligência sobre a operação comercial.
          </p>

          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="https://app.cti-intelligence.com/dashboard" className="inline-flex items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3.5 font-bold text-[#02111d] shadow-[0_18px_50px_rgba(34,211,238,.18)] transition hover:-translate-y-0.5 hover:bg-cyan-300">
              Entrar no CTI Web <ArrowRight size={18} />
            </Link>
            <a href="#filosofia" className="inline-flex items-center gap-2 rounded-2xl border border-white/12 bg-white/[.03] px-5 py-3.5 font-semibold text-white transition hover:border-white/25 hover:bg-white/[.06]">
              Conhecer a filosofia
            </a>
          </div>

          <div className="mt-10 grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
            {["Dados", "Território", "Previsão", "Ação"].map((item) => (
              <div key={item} className="rounded-2xl border border-white/8 bg-white/[.025] px-4 py-4 text-sm font-semibold text-slate-300">
                <span className="mb-2 block h-1.5 w-1.5 rounded-full bg-cyan-300" />{item}
              </div>
            ))}
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-0 rounded-[2.5rem] bg-cyan-400/10 blur-3xl" />
          <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#071327]/90 p-5 shadow-2xl shadow-black/40 sm:p-7">
            <div className="flex items-center justify-between border-b border-white/8 pb-5">
              <div>
                <p className="text-xs uppercase tracking-[.2em] text-cyan-300">CTI Intelligence Layer</p>
                <h2 className="mt-2 text-xl font-bold">Do sinal à decisão</h2>
              </div>
              <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/8 px-3 py-2 text-xs font-semibold text-emerald-300">Núcleo conectado</div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <SignalCard icon={Radar} label="Mercado" value="Sinais externos" />
              <SignalCard icon={Route} label="Operação" value="Ações comerciais" />
              <SignalCard icon={ChartNoAxesCombined} label="Histórico" value="Padrões e evolução" />
              <SignalCard icon={Target} label="Prioridade" value="Próxima decisão" />
            </div>

            <div className="mt-5 rounded-2xl border border-cyan-400/15 bg-cyan-400/[.04] p-5">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-xl bg-cyan-400/10 p-2 text-cyan-300"><BrainCircuit size={20} /></div>
                <div>
                  <p className="text-sm font-bold text-white">Inteligência aplicada ao contexto</p>
                  <p className="mt-1 text-sm leading-6 text-slate-400">O CTI não apresenta apenas números. Ele organiza sinais para reduzir ruído, evidenciar risco e apoiar a próxima ação comercial.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="filosofia" className="relative border-y border-white/8 bg-white/[.015]">
        <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
          <div className="grid gap-14 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="text-sm font-bold uppercase tracking-[.2em] text-cyan-300">Nossa filosofia</p>
              <h2 className="mt-4 text-4xl font-black tracking-[-.03em] sm:text-5xl">Informação sem contexto é apenas volume.</h2>
              <p className="mt-6 max-w-xl text-lg leading-8 text-slate-400">O CTI foi concebido para unir operação, histórico, mercado e inteligência em uma mesma leitura. O objetivo não é acumular dados. É aumentar a qualidade da decisão.</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {pilares.map(({ icon: Icon, titulo, texto }) => (
                <div key={titulo} className="rounded-3xl border border-white/8 bg-[#071327]/70 p-6 transition hover:-translate-y-1 hover:border-cyan-400/20">
                  <div className="mb-5 inline-flex rounded-2xl border border-cyan-400/15 bg-cyan-400/8 p-3 text-cyan-300"><Icon size={22} /></div>
                  <h3 className="text-lg font-bold">{titulo}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{texto}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="como-funciona" className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-sm font-bold uppercase tracking-[.2em] text-cyan-300">Como funciona</p>
          <h2 className="mt-4 text-4xl font-black tracking-[-.03em] sm:text-5xl">Uma cadeia contínua de inteligência.</h2>
          <p className="mt-5 text-lg leading-8 text-slate-400">O CTI organiza a jornada entre dado bruto e ação comercial em cinco movimentos.</p>
        </div>

        <div className="mt-12 grid gap-3 lg:grid-cols-5">
          {fluxo.map(([numero, titulo, texto], index) => (
            <div key={numero} className="relative rounded-3xl border border-white/8 bg-white/[.025] p-5">
              <div className="mb-8 flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-cyan-300">{numero}</span>
                {index < fluxo.length - 1 && <ArrowRight className="hidden text-slate-700 lg:block" size={18} />}
              </div>
              <h3 className="text-lg font-bold">{titulo}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-400">{texto}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="plataforma" className="border-y border-white/8 bg-[#050d1b]">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 py-24 lg:grid-cols-2 lg:px-8">
          <div className="rounded-[2rem] border border-white/8 bg-[#071327] p-7 sm:p-9">
            <div className="inline-flex rounded-2xl bg-cyan-400/8 p-3 text-cyan-300"><Layers3 size={24} /></div>
            <p className="mt-6 text-sm font-bold uppercase tracking-[.2em] text-cyan-300">CTI Web</p>
            <h3 className="mt-3 text-3xl font-black tracking-tight">Leitura executiva e inteligência.</h3>
            <p className="mt-4 leading-7 text-slate-400">Ambiente para visualizar histórico, desempenho, oportunidades, pipeline, vendas, forecast, território e inteligência comercial em uma visão consolidada.</p>
            <Link href="https://app.cti-intelligence.com/dashboard" className="mt-7 inline-flex items-center gap-2 font-bold text-cyan-300 hover:text-cyan-200">Acessar CTI Web <ArrowRight size={17} /></Link>
          </div>

          <div className="rounded-[2rem] border border-white/8 bg-[#071327] p-7 sm:p-9">
            <div className="inline-flex rounded-2xl bg-emerald-400/8 p-3 text-emerald-300"><UsersRound size={24} /></div>
            <p className="mt-6 text-sm font-bold uppercase tracking-[.2em] text-emerald-300">CRM App</p>
            <h3 className="mt-3 text-3xl font-black tracking-tight">Operação comercial no campo.</h3>
            <p className="mt-4 leading-7 text-slate-400">Ambiente operacional para agenda, clientes, atividades, visitas, oportunidades, propostas, pedidos e vendas, conectado ao mesmo núcleo de informação do CTI.</p>
            <Link href="https://app.cti-intelligence.com/crm-app" className="mt-7 inline-flex items-center gap-2 font-bold text-emerald-300 hover:text-emerald-200">Acessar CRM App <ArrowRight size={17} /></Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[.9fr_1.1fr] lg:items-center">
          <div>
            <p className="text-sm font-bold uppercase tracking-[.2em] text-cyan-300">Capacidade integrada</p>
            <h2 className="mt-4 text-4xl font-black tracking-[-.03em] sm:text-5xl">Uma plataforma. Várias leituras do mesmo negócio.</h2>
            <p className="mt-5 text-lg leading-8 text-slate-400">A operação não precisa escolher entre CRM, relatório ou inteligência. O CTI conecta essas camadas para que a mesma informação continue útil do registro à decisão executiva.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {capacidades.map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[.025] px-4 py-4 text-sm text-slate-300">
                <CheckCircle2 size={18} className="shrink-0 text-cyan-300" /> {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-24 lg:px-8">
        <div className="relative overflow-hidden rounded-[2.2rem] border border-cyan-400/20 bg-gradient-to-br from-cyan-400/12 via-[#071327] to-emerald-400/8 p-8 sm:p-12">
          <div className="absolute right-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-cyan-300/10 blur-3xl" />
          <div className="relative grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 text-sm font-bold uppercase tracking-[.2em] text-cyan-300"><Globe2 size={17} /> CTI Comercial Intelligence</div>
              <h2 className="max-w-3xl text-4xl font-black tracking-[-.03em] sm:text-5xl">Menos ruído. Mais contexto. Decisões comerciais melhores.</h2>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">Acesse o ambiente executivo e acompanhe a operação a partir de uma visão integrada do negócio.</p>
            </div>
            <Link href="https://app.cti-intelligence.com/dashboard" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-6 py-4 font-bold text-[#02111d] transition hover:-translate-y-0.5">Acessar plataforma <ArrowRight size={18} /></Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/8">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div className="flex items-center gap-3"><Gauge size={18} className="text-cyan-300" /><span>CTI — Comercial Intelligence</span></div>
          <div className="flex flex-wrap items-center gap-5">
            <span className="inline-flex items-center gap-2"><LockKeyhole size={15} /> Ambientes protegidos por autenticação</span>
            <span>© 2026 CTI</span>
          </div>
        </div>
      </footer>
    </main>
  )
}

function SignalCard({ icon: Icon, label, value }: { icon: typeof Radar; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/[.025] p-4">
      <Icon size={19} className="text-cyan-300" />
      <p className="mt-4 text-xs uppercase tracking-[.16em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-white">{value}</p>
    </div>
  )
}
