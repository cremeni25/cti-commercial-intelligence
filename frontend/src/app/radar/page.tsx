import Link from "next/link"
import { ArrowLeft, CalendarDays, Radar, ScanSearch } from "lucide-react"
import { radarItems, temasRadar } from "../institutional-data"

export default function RadarPage() {
  return (
    <main className="min-h-screen bg-[#020817] text-white">
      <header className="border-b border-white/8 bg-[#020817]/95">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 lg:px-8">
          <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-400 transition hover:text-white"><ArrowLeft size={17} /> CTI Institutional</Link>
          <span className="text-xs font-bold uppercase tracking-[.18em] text-cyan-300">Radar CTI</span>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-5 py-20 lg:px-8 lg:py-24">
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/18 bg-cyan-400/[.06] px-3 py-1.5 text-xs font-bold uppercase tracking-[.16em] text-cyan-300"><Radar size={14} /> Contexto em movimento</div>
        <h1 className="mt-7 max-w-4xl text-5xl font-black tracking-[-.04em] sm:text-6xl">Radar CTI</h1>
        <p className="mt-6 max-w-4xl text-xl leading-9 text-slate-400">Uma camada editorial para organizar fatos, tecnologia, agenda, regulação e sinais públicos relacionados às verticais acompanhadas pelo CTI. O Radar não substitui a inteligência privada da operação; ele amplia o contexto público ao redor dos negócios.</p>

        <div className="mt-14 grid gap-4 lg:grid-cols-3">
          {radarItems.map((item) => (
            <article key={item.slug} className="rounded-3xl border border-white/8 bg-[#071327]/70 p-6">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-bold uppercase tracking-[.18em] text-cyan-300">{item.categoria}</span>
                <span className="rounded-full border border-white/8 px-2.5 py-1 text-[11px] text-slate-500">{item.status}</span>
              </div>
              <h2 className="mt-6 text-xl font-black">{item.titulo}</h2>
              <p className="mt-4 text-sm leading-6 text-slate-400">{item.resumo}</p>
              <p className="mt-6 text-xs text-slate-600">{item.negocio}</p>
            </article>
          ))}
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
          <div className="rounded-3xl border border-white/8 bg-white/[.018] p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-300"><ScanSearch size={18} className="text-cyan-300" /> Escopo editorial</div>
            <div className="mt-5 flex flex-wrap gap-2">{temasRadar.map((tema) => <span key={tema} className="rounded-full border border-white/8 bg-[#071327]/55 px-3 py-2 text-xs text-slate-400">{tema}</span>)}</div>
          </div>
          <div className="rounded-3xl border border-white/8 bg-white/[.018] p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-300"><CalendarDays size={18} className="text-emerald-300" /> Evolução prevista</div>
            <p className="mt-4 text-sm leading-6 text-slate-400">A próxima evolução do Radar é conectar fontes públicas confiáveis, datar as publicações, classificar cada item por vertical e permitir que novas operações tenham seu próprio fluxo de contexto sem misturar informações entre negócios.</p>
          </div>
        </div>
      </section>
    </main>
  )
}
