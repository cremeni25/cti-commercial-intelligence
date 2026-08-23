import Link from "next/link"
import { ArrowLeft, CalendarDays, Radar, ScanSearch } from "lucide-react"
import { radarItems, temasRadar } from "../institutional-data"

export default function RadarPage() {
  return (
    <main className="min-h-screen bg-[#f6f5f1] text-[#172033]">
      <header className="border-b border-[#d9dce3] bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 lg:px-8">
          <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#667085] transition hover:text-[#123b5d]"><ArrowLeft size={17} /> CTI Institutional</Link>
          <span className="text-xs font-bold uppercase tracking-[.18em] text-[#176b8e]">Radar CTI</span>
        </div>
      </header>

      <section className="border-b border-[#d9dce3] bg-white">
        <div className="mx-auto max-w-6xl px-5 py-20 lg:px-8 lg:py-24">
          <div className="inline-flex items-center gap-2 rounded-full bg-[#eaf3f8] px-3 py-1.5 text-xs font-bold uppercase tracking-[.16em] text-[#176b8e]"><Radar size={14} /> Contexto em movimento</div>
          <h1 className="mt-7 max-w-4xl text-5xl font-black tracking-[-.04em] text-[#172033] sm:text-6xl">Radar CTI</h1>
          <p className="mt-6 max-w-4xl text-xl leading-9 text-[#5f6b7a]">Uma camada editorial para organizar fatos, tecnologia, agenda, regulação e sinais públicos relacionados às verticais acompanhadas pelo CTI. O Radar não substitui a inteligência privada da operação; ele amplia o contexto público ao redor dos negócios.</p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 lg:px-8 lg:py-20">
        <div className="grid gap-4 lg:grid-cols-3">
          {radarItems.map((item) => (
            <article key={item.slug} className="rounded-3xl border border-[#d6dde3] bg-white p-6 shadow-[0_12px_30px_rgba(20,40,60,.04)]">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-bold uppercase tracking-[.18em] text-[#176b8e]">{item.categoria}</span>
                <span className="rounded-full bg-[#f1f3f5] px-2.5 py-1 text-[11px] text-[#7a8494]">{item.status}</span>
              </div>
              <h2 className="mt-6 text-xl font-black text-[#172033]">{item.titulo}</h2>
              <p className="mt-4 text-sm leading-6 text-[#5f6b7a]">{item.resumo}</p>
              <p className="mt-6 text-xs text-[#8a95a3]">{item.negocio}</p>
            </article>
          ))}
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
          <div className="rounded-3xl border border-[#d7dde4] bg-white p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-[#39475a]"><ScanSearch size={18} className="text-[#176b8e]" /> Escopo editorial</div>
            <div className="mt-5 flex flex-wrap gap-2">{temasRadar.map((tema) => <span key={tema} className="rounded-full bg-[#f1f3f5] px-3 py-2 text-xs text-[#667085]">{tema}</span>)}</div>
          </div>
          <div className="rounded-3xl border border-[#d7dde4] bg-[#eef2f4] p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-[#39475a]"><CalendarDays size={18} className="text-[#3f7a5e]" /> Evolução prevista</div>
            <p className="mt-4 text-sm leading-6 text-[#5f6b7a]">A próxima evolução do Radar é conectar fontes públicas confiáveis, datar as publicações, classificar cada item por vertical e permitir que novas operações tenham seu próprio fluxo de contexto sem misturar informações entre negócios.</p>
          </div>
        </div>
      </section>
    </main>
  )
}
