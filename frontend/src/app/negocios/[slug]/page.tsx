import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft, ArrowRight, BriefcaseBusiness, LockKeyhole, Radar } from "lucide-react"
import { negocios } from "../../institutional-data"

export function generateStaticParams() {
  return negocios.map((negocio) => ({ slug: negocio.slug }))
}

export default async function NegocioPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const negocio = negocios.find((item) => item.slug === slug)
  if (!negocio) notFound()

  return (
    <main className="min-h-screen bg-[#f6f5f1] text-[#172033]">
      <header className="border-b border-[#d9dce3] bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 lg:px-8">
          <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#667085] transition hover:text-[#123b5d]"><ArrowLeft size={17} /> CTI Institutional</Link>
          <span className="text-xs font-bold uppercase tracking-[.18em] text-[#176b8e]">Negócios</span>
        </div>
      </header>

      <section className="border-b border-[#d9dce3] bg-white">
        <div className="mx-auto max-w-6xl px-5 py-20 lg:px-8 lg:py-24">
          <div className="inline-flex items-center gap-2 rounded-full bg-[#e8f4ed] px-3 py-1.5 text-xs font-bold uppercase tracking-[.16em] text-[#2d6b4d]"><BriefcaseBusiness size={14} /> {negocio.status}</div>
          <p className="mt-8 text-sm font-bold uppercase tracking-[.2em] text-[#176b8e]">{negocio.nome}</p>
          <h1 className="mt-3 max-w-4xl text-5xl font-black tracking-[-.04em] text-[#172033] sm:text-6xl">{negocio.parceiro}</h1>
          <p className="mt-7 max-w-4xl text-xl leading-9 text-[#5f6b7a]">{negocio.descricao}</p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 lg:px-8 lg:py-20">
        <div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
          <div className="rounded-[2rem] border border-[#d7dde4] bg-white p-7 sm:p-9">
            <p className="text-sm font-bold uppercase tracking-[.18em] text-[#176b8e]">Eixos de inteligência</p>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {negocio.eixos.map((eixo) => <div key={eixo} className="rounded-2xl border border-[#d9dfe6] bg-[#fafafa] px-4 py-4 text-sm leading-6 text-[#39475a]">{eixo}</div>)}
            </div>
          </div>

          <div className="rounded-[2rem] border border-[#d7dde4] bg-[#eef2f4] p-7 sm:p-9">
            <div className="flex items-center gap-2 text-sm font-bold text-[#39475a]"><Radar size={18} className="text-[#176b8e]" /> Temas públicos relacionados</div>
            <div className="mt-6 flex flex-wrap gap-2">{negocio.temas.map((tema) => <span key={tema} className="rounded-full bg-white px-3 py-2 text-xs text-[#667085]">{tema}</span>)}</div>
            <Link href="/radar" className="mt-8 inline-flex items-center gap-2 text-sm font-bold text-[#176b8e] hover:text-[#0f4f6d]">Abrir Radar CTI <ArrowRight size={16} /></Link>
          </div>
        </div>

        <div className="mt-8 rounded-3xl border border-[#d7dde4] bg-white p-6">
          <div className="flex items-start gap-3">
            <LockKeyhole size={18} className="mt-0.5 shrink-0 text-[#7a8494]" />
            <div>
              <p className="text-sm font-bold text-[#39475a]">Separação entre informação institucional e operação</p>
              <p className="mt-2 text-sm leading-6 text-[#667085]">Esta página apresenta somente o contexto público da vertical. Carteira, clientes, vendas, metas, oportunidades, forecast, recomendações e demais informações estratégicas permanecem nos ambientes autenticados do CTI.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
