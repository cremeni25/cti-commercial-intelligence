import Link from "next/link"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

const atalhos = [
  { href: "/atividades/interacao", titulo: "Nova interação", apoio: "Registrar visita, ligação, reunião, WhatsApp ou follow-up." },
  { href: "/oportunidades", titulo: "Oportunidades", apoio: "Continuar os negócios comerciais em andamento." },
  { href: "/pipeline", titulo: "Pipeline", apoio: "Acompanhar estágio, valor e próximos passos." },
  { href: "/propostas", titulo: "Propostas", apoio: "Elaborar e acompanhar propostas comerciais." },
  { href: "/pedidos", titulo: "Pedidos", apoio: "Acompanhar pedidos gerados a partir das negociações." },
  { href: "/vendas", titulo: "Vendas", apoio: "Consultar conversões e resultados comerciais." },
  { href: "/atividades", titulo: "Atividades", apoio: "Ver compromissos e acompanhamentos pendentes." },
  { href: "/forecast", titulo: "Forecast", apoio: "Consultar previsão comercial e negócios em curso." },
]

export default function DashboardPage() {
  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Operação comercial</p>
            <h1 className="mt-1 text-3xl font-bold">CTI Comercial</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">
              Acesso direto às funções operacionais. O Mapa Estratégico permanece disponível como leitura analítica, sem bloquear a operação do CTI.
            </p>
          </header>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {atalhos.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-2xl border border-[#17304d] bg-[#071226] p-5 transition hover:border-cyan-500/60 hover:bg-cyan-500/5"
              >
                <strong className="text-base text-white">{item.titulo}</strong>
                <span className="mt-2 block text-sm leading-6 text-slate-400">{item.apoio}</span>
              </Link>
            ))}
          </section>

          <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-semibold">Mapa Comercial Estratégico</h2>
                <p className="mt-1 text-sm text-slate-400">Leitura analítica de mercado, regiões, linhas e perdas.</p>
              </div>
              <Link href="/mapa-estrategico" className="rounded-xl border border-cyan-700 px-4 py-3 text-center text-sm font-semibold text-cyan-300 hover:bg-cyan-950/30">
                Abrir mapa
              </Link>
            </div>
          </section>
        </div>
      </section>
    </main>
  )
}
