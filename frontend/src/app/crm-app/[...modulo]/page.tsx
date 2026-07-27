import Link from "next/link"
import { ArrowLeft, Construction } from "lucide-react"

const nomes: Record<string, string> = {
  agenda: "Agenda comercial",
  clientes: "Clientes",
  visitas: "Visitas",
  oportunidades: "Oportunidades",
  pipeline: "Pipeline",
  atividades: "Atividades",
  nova: "Novo registro",
}

export default async function CrmModuloPage({ params }: { params: Promise<{ modulo: string[] }> }) {
  const { modulo } = await params
  const titulo = modulo.map((segmento) => nomes[segmento] || segmento).join(" — ")

  return (
    <main className="min-h-screen bg-[#020817] px-4 py-6 text-white">
      <div className="mx-auto w-full max-w-xl">
        <Link href="/crm-app" className="inline-flex items-center gap-2 text-sm text-cyan-300">
          <ArrowLeft size={18} /> Voltar ao CRM
        </Link>

        <section className="mt-6 rounded-3xl border border-[#16325c] bg-[#091a33] p-6 shadow-xl">
          <span className="inline-flex rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Construction size={26} /></span>
          <p className="mt-5 text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">Etapa 19</p>
          <h1 className="mt-2 text-2xl font-bold capitalize">{titulo}</h1>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            Módulo integrado à fundação do App CRM. A próxima entrega conectará este fluxo às tabelas, API, território do usuário e sincronização online do CTI.
          </p>
        </section>
      </div>
    </main>
  )
}
