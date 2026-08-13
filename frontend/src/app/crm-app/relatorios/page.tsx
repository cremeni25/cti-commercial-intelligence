import Link from "next/link"
import { ArrowLeft, BarChart3, Bot, ClipboardList, FileDown, LineChart, Users } from "lucide-react"

const relatorios = [
  {
    tema: "pipeline",
    titulo: "Pipeline executivo",
    descricao: "Etapas, valores, negócios sem interação e fechamentos vencidos.",
    icon: BarChart3,
    prompt: "RELATÓRIO CRM — PIPELINE EXECUTIVO. Esta é uma consulta factual nova e independente. Gere um relatório executivo em PDF exclusivamente sobre o pipeline comercial atual do CTI. Faça uma única leitura das fontes CTI necessárias para este tema e congele esse snapshot para toda a entrega. Apresente quantidade e valor por etapa, valor ponderado, negócios sem interação registrada, fechamentos previstos vencidos, principais riscos e prioridades. Inclua gráfico por etapa e disponibilize o PDF e o gráfico para download. Não reutilize números, pesquisa ou snapshot de outro relatório ou conversa.",
  },
  {
    tema: "atividades",
    titulo: "Atividades comerciais",
    descricao: "Pendências, concluídas, atrasos, tipos de interação e próximos encaminhamentos.",
    icon: ClipboardList,
    prompt: "RELATÓRIO CRM — ATIVIDADES COMERCIAIS. Esta é uma consulta factual nova e independente. Gere um relatório executivo em PDF exclusivamente sobre as atividades comerciais do CTI. Faça uma única leitura das fontes CTI necessárias para este tema e use o mesmo snapshot para texto, gráficos e PDF. Separe atividades pendentes, concluídas e atrasadas, apresente distribuição por tipo de atividade, clientes com maior volume de interações, principais pendências e próximos encaminhamentos. Inclua gráficos e disponibilize os artefatos para download. Não reutilize números, pesquisa ou snapshot de outro relatório ou conversa.",
  },
  {
    tema: "forecast",
    titulo: "Forecast comercial",
    descricao: "Projeção por competência, total, ponderado e riscos de fechamento.",
    icon: LineChart,
    prompt: "RELATÓRIO CRM — FORECAST COMERCIAL. Esta é uma consulta factual nova e independente. Gere um relatório executivo em PDF exclusivamente sobre o forecast comercial atual do CTI. Faça uma única leitura das fontes CTI necessárias para este tema e congele um único snapshot. Apresente projeção por competência, valor total, valor ponderado, probabilidade, negócios com fechamento vencido ou sem próxima ação e os principais riscos para a previsão. Inclua gráficos de evolução por competência e disponibilize PDF e gráficos para download. Não reutilize números, pesquisa ou snapshot de outro relatório ou conversa.",
  },
  {
    tema: "carteira",
    titulo: "Carteira de clientes",
    descricao: "Clientes com negócios ativos, lacunas de interação e prioridades comerciais.",
    icon: Users,
    prompt: "RELATÓRIO CRM — CARTEIRA DE CLIENTES. Esta é uma consulta factual nova e independente. Gere um relatório executivo em PDF exclusivamente sobre a carteira de clientes do CRM CTI. Faça uma única leitura das fontes CTI necessárias para este tema e use um único snapshot para toda a entrega. Destaque clientes com oportunidades abertas, clientes sem interação recente quando essa informação estiver disponível, valor de negócios por cliente, principais prioridades comerciais e riscos. Inclua gráficos adequados e disponibilize o PDF e os gráficos para download. Não reutilize números, pesquisa ou snapshot de outro relatório ou conversa.",
  },
] as const

function destino(tema: string, titulo: string, prompt: string) {
  return `/ia-comercial?nova=1&relatorio=${encodeURIComponent(titulo)}&tema=${encodeURIComponent(tema)}&prompt=${encodeURIComponent(prompt)}`
}

export default function RelatoriosCrmPage() {
  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6">
    <div className="mx-auto max-w-6xl">
      <header className="mb-5 flex items-center gap-3">
        <Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
        <div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM · IA-009</p><h1 className="text-2xl font-bold">Central de Relatórios</h1><p className="text-sm text-slate-400">Cada modelo abre um contexto próprio; texto, gráfico e PDF usam somente o snapshot daquele tema.</p></div>
      </header>

      <section className="mb-5 rounded-3xl border border-emerald-900/70 bg-emerald-950/20 p-5">
        <div className="flex items-start gap-3"><Bot className="mt-1 shrink-0 text-emerald-300"/><div><h2 className="font-bold text-emerald-200">Um relatório, uma leitura, um contexto isolado</h2><p className="mt-1 text-sm leading-6 text-emerald-100/70">Ao abrir um modelo, o CRM cria uma nova conversa exclusiva para aquele tema. Pipeline, Atividades, Forecast e Carteira não compartilham pesquisa nem snapshot entre si. A IA-009 continua responsável pelos gráficos, PDF e downloads auditáveis.</p></div></div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">{relatorios.map(({tema,titulo,descricao,icon:Icon,prompt}) => <Link key={tema} href={destino(tema,titulo,prompt)} className="group rounded-3xl border border-[#16325c] bg-[#07162b] p-5 transition hover:border-cyan-600">
        <div className="flex items-start gap-4"><span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-cyan-950/50 text-cyan-300"><Icon size={22}/></span><div className="min-w-0"><h2 className="text-lg font-bold group-hover:text-cyan-200">{titulo}</h2><p className="mt-1 text-sm leading-6 text-slate-400">{descricao}</p><span className="mt-4 inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-3 py-2 text-xs font-bold text-slate-950"><FileDown size={15}/>Preparar relatório</span></div></div>
      </Link>)}</section>

      <section className="mt-5 rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
        <h2 className="font-bold">Relatório personalizado</h2><p className="mt-1 text-sm text-slate-400">Para uma análise fora dos modelos acima, abra a IA Comercial e descreva naturalmente o relatório, gráfico ou PDF que precisa.</p><Link href="/ia-comercial" className="mt-4 inline-flex items-center gap-2 rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-200"><Bot size={17}/>Abrir IA Comercial</Link>
      </section>
    </div>
  </main>
}
