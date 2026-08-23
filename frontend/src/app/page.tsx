import Link from "next/link"
import {
  ArrowRight,
  BriefcaseBusiness,
  CalendarDays,
  Gauge,
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
    <main className="min-h-screen bg-[#f6f5f1] text-[#172033] selection:bg-sky-200">
      <header className="sticky top-0 z-50 border-b border-[#d9dce3] bg-[#f6f5f1]/95 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#123b5d] text-sm font-black text-white">CTI</div>
            <div>
              <div className="text-sm font-semibold tracking-[.16em] text-[#172033]">COMERCIAL INTELLIGENCE</div>
              <div className="text-[10px] uppercase tracking-[.22em] text-[#7a8494]">Inteligência para decisão</div>
            </div>
          </Link>
          <nav className="hidden items-center gap-7 text-sm text-[#667085] md:flex">
            <a href="#o-cti" className="transition hover:text-[#123b5d]">O CTI</a>
            <a href="#negocios" className="transition hover:text-[#123b5d]">Negócios</a>
            <a href="#radar" className="transition hover:text-[#123b5d]">Radar CTI</a>
            <a href="#metodo" className="transition hover:text-[#123b5d]">Como atua</a>
          </nav>
        </div>
      </header>

      <section className="border-b border-[#d9dce3] bg-white">
        <div className="mx-auto grid min-h-[72vh] max-w-7xl items-center gap-14 px-5 py-20 lg:grid-cols-[1.08fr_.92fr] lg:px-8 lg:py-24">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#eaf3f8] px-3 py-1.5 text-xs font-semibold uppercase tracking-[.18em] text-[#245d7e]">
              <Sparkles size={14} /> Inteligência comercial aplicada a negócios reais
            </div>
            <h1 className="max-w-4xl text-5xl font-black leading-[1.02] tracking-[-.045em] text-[#172033] sm:text-6xl lg:text-7xl">
              O CTI transforma <span className="text-[#176b8e]">informação em direção comercial.</span>
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-[#5f6b7a] sm:text-xl">
              Uma plataforma de inteligência comercial criada para acompanhar negócios, organizar sinais relevantes e apoiar decisões com contexto, histórico, mercado e execução na mesma leitura.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a href="#o-cti" className="inline-flex items-center gap-2 rounded-2xl bg-[#123b5d] px-5 py-3.5 font-semibold text-white transition hover:bg-[#0d304d]">
                Entender o CTI <ArrowRight size={18} />
              </a>
              <a href="#negocios" className="inline-flex items-center gap-2 rounded-2xl border border-[#cdd5df] bg-white px-5 py-3.5 font-semibold text-[#243247] transition hover:border-[#123b5d]">
                Ver negócios <BriefcaseBusiness size={18} />
              </a>
            </div>
          </div>

          <div className="rounded-[2rem] border border-[#dfe3e8] bg-[#eef2f4] p-6 shadow-[0_24px_80px_rgba(20,40,60,.08)] sm:p-8">
            <p className="text-xs font-bold uppercase tracking-[.2em] text-[#176b8e]">Leitura CTI</p>
            <h2 className="mt-3 text-2xl font-black text-[#172033]">Um negócio é mais do que seus números.</h2>
            <p className="mt-4 leading-7 text-[#5f6b7a]">O CTI observa a operação como um sistema: fatos comerciais, mercado, território, histórico, agenda, tecnologia e sinais externos passam a compor a mesma leitura.</p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {["Operação", "Mercado", "Histórico", "Contexto"].map((item) => (
                <div key={item} className="rounded-2xl border border-[#d7dde4] bg-white px-4 py-4 text-sm font-semibold text-[#39475a]">
                  <span className="mb-3 block h-1.5 w-8 rounded-full bg-[#5fa6be]" />{item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="o-cti" className="border-b border-[#d9dce3] bg-[#f6f5f1]">
        <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-[.8fr_1.2fr] lg:items-start">
            <div>
              <p className="text-sm font-bold uppercase tracking-[.2em] text-[#176b8e]">O que é o CTI</p>
              <h2 className="mt-4 text-4xl font-black tracking-[-.03em] text-[#172033] sm:text-5xl">Inteligência comercial com contexto.</h2>
            </div>
            <div className="space-y-6 text-lg leading-8 text-[#5f6b7a]">
              <p>O CTI — Comercial Intelligence é uma plataforma concebida para transformar dados comerciais dispersos em uma leitura estruturada do negócio. Ele reúne operação, histórico, território, mercado e inteligência para que a informação deixe de ser apenas registro e passe a orientar prioridade, acompanhamento, previsão e decisão.</p>
              <p>Seu propósito não é substituir pessoas por números, nem acumular indicadores. É criar contexto suficiente para que vendedores, gestores e direção compreendam o que aconteceu, o que está acontecendo e onde a atenção comercial deve estar em seguida.</p>
              <div className="grid gap-3 pt-2 sm:grid-cols-2">
                {["Fonte estruturada de informação", "Leitura territorial e histórica", "Inteligência aplicada ao negócio", "Governança e acesso por perfil"].map((item) => (
                  <div key={item} className="rounded-2xl border border-[#d9dfe6] bg-white px-4 py-4 text-sm font-semibold text-[#39475a]">{item}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="negocios" className="bg-white">
        <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-bold uppercase tracking-[.2em] text-[#176b8e]">Negócios sob inteligência CTI</p>
              <h2 className="mt-4 text-4xl font-black tracking-[-.03em] text-[#172033] sm:text-5xl">Cada vertical tem seu próprio contexto.</h2>
              <p className="mt-5 text-lg leading-8 text-[#5f6b7a]">O CTI pode acompanhar operações distintas sem misturar suas regras, dados ou objetivos. A estrutura nasce preparada para novas verticais conforme novos negócios forem incorporados.</p>
            </div>
            <div className="rounded-2xl bg-[#edf6f1] px-4 py-3 text-sm font-semibold text-[#2d6b4d]">1 vertical ativa · arquitetura expansível</div>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-[1.2fr_.8fr]">
            <Link href={`/negocios/${negocioPrincipal.slug}`} className="group rounded-[2rem] border border-[#cfd9df] bg-[#eef4f7] p-7 transition hover:-translate-y-1 hover:border-[#7aa9bc] sm:p-9">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="rounded-full bg-[#e8f4ed] px-3 py-1.5 text-xs font-bold uppercase tracking-[.15em] text-[#2d6b4d]">{negocioPrincipal.status}</span>
                <ArrowRight className="text-[#176b8e] transition group-hover:translate-x-1" size={20} />
              </div>
              <p className="mt-8 text-sm font-bold uppercase tracking-[.18em] text-[#176b8e]">{negocioPrincipal.nome}</p>
              <h3 className="mt-2 text-3xl font-black text-[#172033]">{negocioPrincipal.parceiro}</h3>
              <p className="mt-5 max-w-3xl text-base leading-7 text-[#5f6b7a]">{negocioPrincipal.resumo}</p>
              <div className="mt-7 flex flex-wrap gap-2">
                {negocioPrincipal.temas.slice(0, 4).map((tema) => <span key={tema} className="rounded-full border border-[#d1d9df] bg-white px-3 py-1.5 text-xs text-[#667085]">{tema}</span>)}
              </div>
            </Link>

            <div className="rounded-[2rem] border border-dashed border-[#cbd2d9] bg-[#fafafa] p-7 sm:p-9">
              <BriefcaseBusiness className="text-[#8a95a3]" size={28} />
              <p className="mt-6 text-sm font-bold uppercase tracking-[.18em] text-[#7a8494]">Novas verticais</p>
              <h3 className="mt-2 text-2xl font-black text-[#172033]">A estrutura não termina no primeiro negócio.</h3>
              <p className="mt-4 leading-7 text-[#5f6b7a]">Equipamentos usados, consórcios ou outras operações poderão entrar como novas verticais, cada uma com identidade, contexto, indicadores e radar próprios.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="radar" className="border-y border-[#d9dce3] bg-[#edf1f3]">
        <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-bold uppercase tracking-[.2em] text-[#176b8e]">Radar CTI</p>
              <h2 className="mt-4 text-4xl font-black tracking-[-.03em] text-[#172033] sm:text-5xl">O que está mudando ao redor dos negócios.</h2>
              <p className="mt-5 text-lg leading-8 text-[#5f6b7a]">O Radar organiza acontecimentos, tecnologia, agenda e sinais públicos que ajudam a compreender o contexto das verticais acompanhadas.</p>
            </div>
            <Link href="/radar" className="inline-flex items-center gap-2 font-bold text-[#176b8e] transition hover:text-[#0f4f6d]">Abrir Radar CTI <ArrowRight size={18} /></Link>
          </div>

          <div className="mt-12 grid gap-4 lg:grid-cols-3">
            {radarItems.map((item) => (
              <article key={item.slug} className="rounded-3xl border border-[#d6dde3] bg-white p-6 shadow-[0_12px_30px_rgba(20,40,60,.04)]">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-bold uppercase tracking-[.18em] text-[#176b8e]">{item.categoria}</span>
                  <span className="rounded-full bg-[#f1f3f5] px-2.5 py-1 text-[11px] text-[#7a8494]">{item.status}</span>
                </div>
                <h3 className="mt-6 text-xl font-black text-[#172033]">{item.titulo}</h3>
                <p className="mt-4 text-sm leading-6 text-[#5f6b7a]">{item.resumo}</p>
                <p className="mt-6 text-xs text-[#8a95a3]">{item.negocio}</p>
              </article>
            ))}
          </div>

          <div className="mt-6 rounded-3xl border border-[#d6dde3] bg-white p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-[#39475a]"><ScanSearch size={18} className="text-[#176b8e]" /> Temas acompanhados pelo Radar</div>
            <div className="mt-4 flex flex-wrap gap-2">{temasRadar.map((tema) => <span key={tema} className="rounded-full bg-[#f1f3f5] px-3 py-2 text-xs text-[#667085]">{tema}</span>)}</div>
          </div>
        </div>
      </section>

      <section id="metodo" className="bg-white">
        <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-bold uppercase tracking-[.2em] text-[#176b8e]">Como o CTI atua</p>
            <h2 className="mt-4 text-4xl font-black tracking-[-.03em] text-[#172033] sm:text-5xl">Do fato à decisão, sem perder o contexto.</h2>
          </div>
          <div className="mt-12 grid gap-3 lg:grid-cols-5">
            {fluxo.map(([numero, titulo, texto]) => (
              <div key={numero} className="rounded-3xl border border-[#d9dfe6] bg-[#fafafa] p-5">
                <span className="font-mono text-xs font-bold text-[#176b8e]">{numero}</span>
                <h3 className="mt-8 text-lg font-bold text-[#172033]">{titulo}</h3>
                <p className="mt-3 text-sm leading-6 text-[#5f6b7a]">{texto}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-[#d9dce3] bg-[#f6f5f1]">
        <div className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-3xl border border-[#d7dde4] bg-white p-6">
              <div className="flex items-center gap-2 text-sm font-bold text-[#39475a]"><TrendingUp size={18} className="text-[#176b8e]" /> Mercado em números</div>
              <p className="mt-4 text-sm leading-6 text-[#5f6b7a]">Indicadores econômicos e setoriais relacionados às verticais serão incorporados somente quando houver fonte pública confiável e contexto de uso. O espaço já está reservado para evolução sem inserir números decorativos.</p>
            </div>
            <div className="rounded-3xl border border-[#d7dde4] bg-white p-6">
              <div className="flex items-center gap-2 text-sm font-bold text-[#39475a]"><CalendarDays size={18} className="text-[#3f7a5e]" /> Agenda e acontecimentos</div>
              <p className="mt-4 text-sm leading-6 text-[#5f6b7a]">Feiras, treinamentos, lançamentos e movimentos relevantes passam a compor o contexto público das verticais, conectados ao Radar CTI e sem exposição de informações comerciais internas.</p>
            </div>
          </div>

          <div className="mt-12 rounded-3xl border border-[#cfd6dd] bg-white p-6 sm:p-7" aria-label="Acesso restrito">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[.18em] text-[#7a8494]"><LockKeyhole size={15} /> Acesso restrito</div>
                <p className="mt-2 text-sm leading-6 text-[#667085]">Ambientes operacionais disponíveis exclusivamente para usuários autorizados do CTI.</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[31rem]">
                <Link href="https://app.cti-intelligence.com/dashboard" className="group flex items-center justify-between rounded-2xl border border-[#d5dce3] bg-[#fafafa] px-4 py-3.5 transition hover:border-[#6e9bb0]">
                  <span><span className="block text-sm font-bold text-[#243247]">CTI Web</span><span className="mt-0.5 block text-xs text-[#8a95a3]">Ambiente executivo</span></span><ArrowRight size={16} className="text-[#8a95a3] group-hover:text-[#176b8e]" />
                </Link>
                <Link href="https://app.cti-intelligence.com/crm-app" className="group flex items-center justify-between rounded-2xl border border-[#d5dce3] bg-[#fafafa] px-4 py-3.5 transition hover:border-[#7eaa91]">
                  <span><span className="block text-sm font-bold text-[#243247]">CRM App</span><span className="mt-0.5 block text-xs text-[#8a95a3]">Ambiente operacional</span></span><ArrowRight size={16} className="text-[#8a95a3] group-hover:text-[#3f7a5e]" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#d9dce3] bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 text-sm text-[#7a8494] sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div className="flex items-center gap-3"><Gauge size={18} className="text-[#176b8e]" /><span>CTI — Comercial Intelligence</span></div>
          <span>© 2026 CTI</span>
        </div>
      </footer>
    </main>
  )
}
