"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type RegistroNucleo = {
  oportunidade_id?: string
  etapa?: string
  valor?: number
  valor_ponderado?: number
  proposta_id?: string | null
  pedido_id?: string | null
}

type EstadoTeste = "carregando" | "aprovado" | "alerta" | "falha"

const modulos = [
  { nome: "Dashboard Executivo", rota: "/dashboard", objetivo: "Validar indicadores comerciais consolidados e preservação dos relógios históricos." },
  { nome: "Pipeline", rota: "/pipeline", objetivo: "Conferir etapa, cliente, valor e probabilidade de cada oportunidade." },
  { nome: "Forecast", rota: "/forecast", objetivo: "Conferir pipeline total e ponderado por competência e responsável." },
  { nome: "Funil Carrier", rota: "/funil-carrier", objetivo: "Conferir o avanço do pedido até dossiê, Carrier e faturamento." },
  { nome: "Pedidos", rota: "/pedidos", objetivo: "Conferir pedido, proposta, aceite, equipamento e dossiê operacional." },
  { nome: "IA Comercial", rota: "/ia-comercial", objetivo: "Conferir prioridades e recomendações auditáveis baseadas no núcleo CRM." },
]

export default function HomologacaoCrmPage() {
  const [estado, setEstado] = useState<EstadoTeste>("carregando")
  const [registros, setRegistros] = useState<RegistroNucleo[]>([])
  const [mensagem, setMensagem] = useState("Testando conexão com o núcleo comercial...")
  const [ultimaVerificacao, setUltimaVerificacao] = useState("")

  const executarTeste = async () => {
    setEstado("carregando")
    setMensagem("Testando conexão com o núcleo comercial...")
    try {
      const resposta = await fetch(`${API_URL}/crm/nucleo-comercial`, { cache: "no-store" })
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`)
      const payload = await resposta.json()
      if (!Array.isArray(payload)) throw new Error("Resposta fora do contrato esperado")
      setRegistros(payload)
      setEstado(payload.length > 0 ? "aprovado" : "alerta")
      setMensagem(payload.length > 0
        ? "Núcleo CRM conectado e respondendo com dados comerciais."
        : "Núcleo CRM conectado, porém sem registros comerciais para validar.")
    } catch (erro) {
      setRegistros([])
      setEstado("falha")
      setMensagem(erro instanceof Error ? `Falha de conexão: ${erro.message}` : "Falha de conexão com o núcleo CRM.")
    } finally {
      setUltimaVerificacao(new Date().toLocaleString("pt-BR"))
    }
  }

  useEffect(() => {
    queueMicrotask(() => { void executarTeste() })
  }, [])

  const resumo = useMemo(() => {
    const abertas = registros.filter((item) => !["PERDIDO", "CANCELADO", "FATURADO", "ENCERRADO"].includes(String(item.etapa || "")))
    return {
      total: registros.length,
      abertas: abertas.length,
      propostas: registros.filter((item) => Boolean(item.proposta_id)).length,
      pedidos: registros.filter((item) => Boolean(item.pedido_id)).length,
      valor: abertas.reduce((soma, item) => soma + Number(item.valor || 0), 0),
      ponderado: abertas.reduce((soma, item) => soma + Number(item.valor_ponderado || 0), 0),
    }
  }, [registros])

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Homologação funcional e visual</p>
          <h1 className="mt-2 text-3xl font-bold">Central de Homologação CRM</h1>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">Use esta tela como ponto único de validação. O teste abaixo confirma a comunicação com o núcleo comercial e os cartões abrem cada módulo na sequência recomendada.</p>
        </header>

        <section className={`rounded-3xl border p-6 ${estado === "aprovado" ? "border-emerald-700 bg-emerald-950/20" : estado === "falha" ? "border-red-800 bg-red-950/20" : estado === "alerta" ? "border-amber-700 bg-amber-950/20" : "border-cyan-800 bg-[#071427]"}`}>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold">Status do núcleo CRM: <span className="uppercase">{estado}</span></p>
              <p className="mt-2 text-sm text-slate-300">{mensagem}</p>
              <p className="mt-2 break-all text-xs text-slate-500">Endpoint: {API_URL}/crm/nucleo-comercial</p>
              <p className="mt-1 text-xs text-slate-500">Última verificação: {ultimaVerificacao || "em andamento"}</p>
            </div>
            <button type="button" onClick={() => void executarTeste()} className="rounded-xl border border-cyan-700 px-5 py-3 text-sm font-semibold text-cyan-300">Testar novamente</button>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
          <Kpi titulo="Registros no núcleo" valor={resumo.total} />
          <Kpi titulo="Negócios abertos" valor={resumo.abertas} />
          <Kpi titulo="Com proposta" valor={resumo.propostas} />
          <Kpi titulo="Com pedido" valor={resumo.pedidos} />
          <Kpi titulo="Pipeline aberto" valor={moeda(resumo.valor)} />
          <Kpi titulo="Pipeline ponderado" valor={moeda(resumo.ponderado)} />
        </section>

        <section className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
          {modulos.map((modulo, indice) => <article key={modulo.rota} className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
            <div className="flex items-center justify-between gap-3"><span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300">Etapa {indice + 1}</span><span className="text-xs text-slate-500">{modulo.rota}</span></div>
            <h2 className="mt-4 text-xl font-bold">{modulo.nome}</h2>
            <p className="mt-2 min-h-16 text-sm leading-6 text-slate-400">{modulo.objetivo}</p>
            <Link href={modulo.rota} className="mt-5 inline-flex rounded-xl bg-cyan-500 px-4 py-3 text-sm font-bold text-slate-950">Abrir e homologar</Link>
          </article>)}
        </section>

        <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
          <h2 className="text-xl font-bold">Critério de aprovação</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">Os mesmos negócios devem apresentar cliente, etapa, proposta, pedido, valor e valor ponderado coerentes entre Pipeline, Forecast, Funil Carrier, Pedidos, Dashboard e IA Comercial. Divergências visuais ou funcionais devem ser registradas com a tela e o negócio afetado.</p>
        </section>
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) {
  return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-xs text-slate-400">{titulo}</p><p className="mt-2 text-xl font-bold text-cyan-300">{valor}</p></div>
}

function moeda(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}
