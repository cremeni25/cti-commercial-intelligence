import Link from "next/link"
import {
  ArrowRight,
  BriefcaseBusiness,
  CalendarDays,
  Gauge,
  Layers3,
  LockKeyhole,
  Radar,
  ScanSearch,
  Sparkles,
  TrendingUp,
} from "lucide-react"
import { negocios, radarItems, temasRadar } from "./institutional-data"

const fluxo = [
  ["01", "Capturar", "Reunir dados, sinais e fatos relevantes de cada negócio."],
  ["02", "Contextualizar", "Relacionar território, histórico, operação, mercado e momento comercial."],
  ["03", "Interpretar", "Transformar volume de informação em leitura objetiva."],
  ["04", "Priorizar", "Evidenciar o que exige atenção, oportunidade ou ação."],
  ["05", "Executar", "Conectar decisão, acompanhamento e operação comercial."],
]

export default function HomePage() {
  const negocioPrincipal = negocios[0]

  return (
    <main className="min-h-screen bg-[#020817] text-white selection:bg-cyan-400/30">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-[-24rem] h-[54rem] w-[54rem] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute right-[-14rem] top-[28rem] h-[38rem] w-[38rem] rounded-full bg-emerald-500/8 blur-3xl" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/8 bg-[#020817]/88 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl border border-cyan-400/30 bg-cyan-400/10 text-sm font-black text-cyan-300">CTI</div>
            <div>
              <div className="text-sm font-semibold tracking-[.16em]">COMERCIAL INTELLIGENCE</div>
              <div className="text-[10px] uppercase tracking-[.22em] text-slate-500">Inteligência para decisão</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-7 text-sm text-slate-400 md:flex">
            <a href="#o-cti" className="transition hover:text-white">O CTI</a>
            <a href="#negocios" className="transition hover:text-white">Negócios</a>
            <a href="#radar" className="transition hover:text-white">Radar CTI</a>
            <a href="#metodo" className="transition hover:text-white">Como atua</a>
          </nav>
        </div>
      </header>

      <section className="relative mx-auto grid min-h-[76vh] max-w-7xl items-center gap-14 px-5 py-20 lg:grid-cols-[1.08fr_.92fr] lg:px-8 lg:py-24">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/8 px-3 py-1.5 text-xs font-semibold uppercase tracking-[.18em] text-cyan-300">
            <Sparkles size={14} /> Inteligência comercial aplicada a negócios reais
          </div>
          <h1 className="max-w-4xl text-5xl font-black leading-[1.02] tracking-[-.045em] sm:text-6xl lg:text-7xl">
            O CTI transforma <span className="bg-gradient-to-r from-cyan-300 via-sky-300 to-emerald-300 bg-clip-text text-transparent">informação em direção comercial.</span>
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-400 sm:text-xl">
            Uma plataforma de inteligência comercial criada para acompanhar negócios, organizar sinais relevantes e apoiar decisões com contexto, histórico, mercado e execução na mesma leitura.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <a href="#o-cti" className="inline-flex items-center gap-2 rounded-2xl border border-white/12 bg-white/[.03] px-5 py-3.5 font-semibold transition hover:border-white/25 hover:bg-white/[.06]">
              Entender o CTI <ArrowRight size={18} />
            </a>
            <a href="#negocios" className="inline-flex items-center gap-2 rounded-2xl border border-cyan-400/15 bg-cyan-400/[.05] px-5 py-3.5 font-semibold text-cyan-200 transition hover:border-cyan-400/30">
              Ver negócios <BriefcaseBusiness size={18} />
            </a>
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-0 rounded-[2.5rem] bg-cyan-400/10 blur-3xl" />
          <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#071327]/92 p-6 shadow-2xl shadow-black/40 sm:p-7">
            <p className="text-xs font-bold uppercase tracking-[.2em] text-cyan-300">Leitura CTI</p>
            <h2 className="mt-3 text-2xl font-black">Um negócio é mais do que seus números.</h2>
            <p className="mt-4 leading-7 text-slate-400">O CTI observa a operação como um sistema: fatos comerciais, mercado, território, histórico, agenda, tecnologia e sinais externos passam a compor a mesma leitura.</p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {["Operação", "Mercado", "Histórico", "Contexto"].map((item) => (
                <div key={item} className="rounded-2xl border border-white/8 bg-white/[.025] px-4 py-4 text-sm font-semibold text-slate-300">
                  <span className="mb-3 block h-1.5 w-1.5 rounded-full bg-cyan-300" />{item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="o-cti" className="border-y border-white/8 bg-white/[.015]">
        <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-[.8fr_1.2fr] lg:items-start">
            <div>
              <p className="text-sm font-bold uppercase tracking-[.2em] text-cyan-300">O que é o CTI</p>
              <h2 className="mt-4 text-4xl font-black tracking-[-.03em] sm:text-5xl">Inteligência comercial com contexto.</h2>
            </div>
            <div className="space-y-6 text-lg leading-8 text-slate-400">
              <p>O CTI — Comercial Intelligence é uma plataforma concebida para transformar dados comerciais dispersos em uma leitura estruturada do negócio. Ele reúne operação, histórico, território, mercado e inteligência para que a informação deixe de ser apenas registro e passe a orientar prioridade, acompanhamento, previsão e decisão.</p>
              <p>Seu propósito não é substituir pessoas por números, nem acumular indicadores. É criar contexto suficiente para que vendedores, gestores e direção compreendam o que aconteceu, o que está acontecendo e onde a atenção comercial deve estar em seguida.</p>
              <div className="grid gap-3 pt-2 sm:grid-cols-2">
                {["Fonte estruturada de informação", "Leitura territorial e histórica", "Inteligência aplicada ao negócio", "Governança e acesso por perfil"].map((item) => (
                  <div key={item} className="rounded-2xl border border-white/8 bg-[#071327]/55 px-4 py-4 text-sm font-semibold text-slate-300">{item}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="negocios" className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-bold uppercase tracking-[.2em] text-cyan-300">Negócios sob inteligência CTI</p>
            <h2 className="mt-4 text-4xl font-black tracking-[-.03em] sm:text-5xl">Cada vertical tem seu próprio contexto.</h2>
            <p className="mt-5 text-lg leading-8 text-slate-400">O CTI pode acompanhar operações distintas sem misturar suas regras, dados ou objetivos. A estrutura nasce preparada para novas verticais conforme novos negócios forem incorporados.</p>
          </div>
          <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[.05] px-4 py-3 text-sm font-semibold text-emerald-300">1 vertical ativa · arquitetura expansível</div>
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-[1.2fr_.8fr]">
          <Link href={`/negocios/${negocioPrincipal.slug}`} className="group rounded-[2rem] border border-cyan-400/18 bg-gradient-to-br from-cyan-400/[.08] via-[#071327] to-[#071327] p-7 transition hover:-translate-y-1 hover:border-cyan-300/30 sm:p-9">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="rounded-full border border-emerald-400/18 bg-emerald-400/[.07] px-3 py-1.5 text-xs font-bold uppercase tracking-[.15em] text-emerald-300">{negocioPrincipal.status}</span>
              <ArrowRight className="text-cyan-300 transition group-hover:translate-x-1" size={20} />
            </div>
            <p className="mt-8 text-sm font-bold uppercase tracking-[.18em] text-cyan-300">{negocioPrincipal.nome}</p>
            <h3 className="mt-2 text-3xl font-black">{negocioPrincipal.parceiro}</h3>
            <p className="mt-5 max-w-3xl text-base leading-7 text-slate-400">{negocioPrincipal.resumo}</p>
            <div className="mt-7 flex flex-wrap gap-2">
              {negocioPrincipal.temas.slice(0, 4).map((tema) => <span key={tema} className="rounded-full border border-white/8 bg-white/[.025] px-3 py-1.5 text-xs text-slate-400">{tema}</span>)}
            </div>
          </Link>

          <div className="rounded-[2rem] border border-dashed border-white/12 bg-white/[.018] p-7 sm:p-9">
            <BriefcaseBusiness className="text-slate-500" size={28} />
            <p className="mt-6 text-sm font-bold uppercase tracking-[.18em] text-slate-500">Novas verticais</p>
            <h3 className="mt-2 text-2xl font-black">A estrutura não termina no primeiro negócio.</h3>
            <p className="mt-4 leading-7 text-slate-400">Equipamentos usados, consórcios ou outras operações poderão entrar como novas verticais, cada uma com identidade, contexto, indicadores e radar próprios.</p>
          </div>
        </div>
      </section>

      <section id="radar" className="border-y border-white/8 bg-[#050d1b]">
        <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-bold uppercase tracking-[.2em] text-cyan-300">Radar CTI</p>
              <h2 className="mt-4 text-4xl font-black tracking-[-.03em] sm:text-5xl">O que está mudando ao redor dos negócios.</h2>
              <p className="mt-5 text-lg leading-8 text-slate-400">O Radar organiza acontecimentos, tecnologia, agenda e sinais públicos que ajudam a compreender o contexto das verticais acompanhadas.</p>
            </div>
            <Link href="/radar" className="inline-flex items-center gap-2 font-bold text-cyan-300 transition hover:text-cyan-200">Abrir Radar CTI <ArrowRight size={18} /></Link>
          </div>

          <div className="mt-12 grid gap-4 lg:grid-cols-3">
            {radarItems.map((item) => (
              <article key={item.slug} className="rounded-3xl border border-white/8 bg-[#071327]/70 p-6">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-bold uppercase tracking-[.18em] text-cyan-300">{item.categoria}</span>
                  <span className="rounded-full border border-white/8 px-2.5 py-1 text-[11px] text-slate-500">{item.status}</span>
                </div>
                <h3 className="mt-6 text-xl font-black">{item.titulo}</h3>
                <p className="mt-4 text-sm leading-6 text-slate-400">{item.resumo}</p>
                <p className="mt-6 text-xs text-slate-600">{item.negocio}</p>
              </article>
            ))}
          </div>

          <div className="mt-6 rounded-3xl border border-white/8 bg-white/[.018] p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-300"><ScanSearch size={18} className="text-cyan-300" /> Temas acompanhados pelo Radar</div>
            <div className="mt-4 flex flex-wrap gap-2">{temasRadar.map((tema) => <span key={tema} className="rounded-full border border-white/8 bg-[#071327]/55 px-3 py-2 text-xs text-slate-400">{tema}</span>)}</div>
          </div>
        </div>
      </section>

      <section id="metodo" className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-sm font-bold uppercase tracking-[.2em] text-cyan-300">Como o CTI atua</p>
          <h2 className="mt-4 text-4xl font-black tracking-[-.03em] sm:text-5xl">Do fato à decisão, sem perder o contexto.</h2>
        </div>
        <div className="mt-12 grid gap-3 lg:grid-cols-5">
          {fluxo.map(([numero, titulo, texto]) => (
            <div key={numero} className="rounded-3xl border border-white/8 bg-white/[.025] p-5">
              <span className="font-mono text-xs font-bold text-cyan-300">{numero}</span>
              <h3 className="mt-8 text-lg font-bold">{titulo}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-400">{texto}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-16 lg:px-8">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-3xl border border-white/8 bg-[#071327]/55 p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-300"><TrendingUp size={18} className="text-cyan-300" /> Mercado em números</div>
            <p className="mt-4 text-sm leading-6 text-slate-400">Indicadores econômicos e setoriais relacionados às verticais serão incorporados somente quando houver fonte pública confiável e contexto de uso. O espaço já está reservado para evolução sem inserir números decorativos.</p>
          </div>
          <div className="rounded-3xl border border-white/8 bg-[#071327]/55 p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-300"><CalendarDays size={18} className="text-emerald-300" /> Agenda e acontecimentos</div>
            <p className="mt-4 text-sm leading-6 text-slate-400">Feiras, treinamentos, lançamentos e movimentos relevantes passam a compor o contexto público das verticais, conectados ao Radar CTI e sem exposição de informações comerciais internas.</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-20 lg:px-8" aria-label="Acesso restrito">
        <div className="rounded-3xl border border-white/8 bg-white/[.018] p-6 sm:p-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[.18em] text-slate-500"><LockKeyhole size={15} /> Acesso restrito</div>
              <p className="mt-2 text-sm leading-6 text-slate-400">Ambientes operacionais disponíveis exclusivamente para usuários autorizados do CTI.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[31rem]">
              <Link href="https://app.cti-intelligence.com/dashboard" className="group flex items-center justify-between rounded-2xl border border-white/8 bg-[#071327]/55 px-4 py-3.5 transition hover:border-cyan-400/20 hover:bg-[#071327]">
                <span><span className="block text-sm font-bold">CTI Web</span><span className="mt-0.5 block text-xs text-slate-500">Ambiente executivo</span></span><ArrowRight size={16} className="text-slate-600 group-hover:text-cyan-300" />
              </Link>
              <Link href="https://app.cti-intelligence.com/crm-app" className="group flex items-center justify-between rounded-2xl border border-white/8 bg-[#071327]/55 px-4 py-3.5 transition hover:border-emerald-400/20 hover:bg-[#071327]">
                <span><span className="block text-sm font-bold">CRM App</span><span className="mt-0.5 block text-xs text-slate-500">Ambiente operacional</span></span><ArrowRight size={16} className="text-slate-600 group-hover:text-emerald-300" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/8">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div className="flex items-center gap-3"><Gauge size={18} className="text-cyan-300" /><span>CTI — Comercial Intelligence</span></div>
          <span>© 2026 CTI</span>
        </div>
      </footer>
    </main>
  )
}
