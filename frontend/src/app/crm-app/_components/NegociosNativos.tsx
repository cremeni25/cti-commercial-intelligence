"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, BriefcaseBusiness, CalendarDays, ChevronRight, Loader2, Search } from "lucide-react"

type Registro = Record<string, unknown>

type Negocio = {
  id: string
  cliente: string
  titulo: string
  etapa: string
  valor: number
  probabilidade: number
  fechamento: string
}

const finais = new Set(["GANHO", "PERDIDO", "CANCELADO", "FATURADO", "ENCERRADO"])

function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const chave of ["dados", "itens", "oportunidades", "resultado"]) {
      if (Array.isArray(objeto[chave])) return objeto[chave] as Registro[]
    }
  }
  return []
}

function texto(valor: unknown) { return String(valor || "").trim() }
function dataBR(valor: string) {
  if (!valor) return "Sem previsão"
  const data = new Date(valor)
  return Number.isNaN(data.getTime()) ? valor : data.toLocaleDateString("pt-BR")
}

export default function NegociosNativos({ modo }: { modo: "oportunidades" | "pipeline" }) {
  const [dados, setDados] = useState<Negocio[]>([])
  const [busca, setBusca] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" })
      .then(async (resposta) => {
        const payload = await resposta.json().catch(() => ({}))
        if (!resposta.ok) throw new Error(String((payload as Registro).detail || `Falha ${resposta.status}`))
        const normalizados = lista(payload).map((item) => ({
          id: texto(item.oportunidade_id || item.id),
          cliente: texto(item.cliente_nome || item.razao_social || item.cliente) || "Cliente em identificação",
          titulo: texto(item.titulo || item.equipamento) || "Negociação comercial",
          etapa: texto(item.etapa || item.status_oportunidade || item.status).toUpperCase() || "OPORTUNIDADE",
          valor: Number(item.valor || item.valor_estimado || 0),
          probabilidade: Number(item.probabilidade || item.probabilidade_fechamento || 0),
          fechamento: texto(item.data_fechamento_prevista || item.fechamento_previsto),
        })).filter((item) => item.id)
        setDados(normalizados)
      })
      .catch((falha) => setErro(falha instanceof Error ? falha.message : "Não foi possível carregar os negócios."))
      .finally(() => setCarregando(false))
  }, [])

  const visiveis = useMemo(() => {
    const base = modo === "oportunidades" ? dados.filter((item) => !finais.has(item.etapa)) : dados
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    return termo ? base.filter((item) => `${item.cliente} ${item.titulo} ${item.etapa}`.toLocaleLowerCase("pt-BR").includes(termo)) : base
  }, [busca, dados, modo])

  const total = visiveis.reduce((soma, item) => soma + item.valor, 0)
  const ponderado = visiveis.reduce((soma, item) => soma + item.valor * (item.probabilidade > 1 ? item.probabilidade / 100 : item.probabilidade), 0)
  const titulo = modo === "pipeline" ? "Pipeline comercial" : "Oportunidades"

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-5xl">
      <header className="mb-5 flex items-center gap-3">
        <Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
        <div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">{titulo}</h1></div>
      </header>

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <Kpi label="Negócios" valor={String(visiveis.length)} />
        <Kpi label="Valor total" valor={total.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} />
        <Kpi label="Valor ponderado" valor={ponderado.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} />
      </div>

      <div className="relative mb-4"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, equipamento ou etapa" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></div>
      {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : visiveis.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum negócio encontrado nesta visão.</div> : <div className="space-y-3">{visiveis.map((item) => <Link key={item.id} href={`/crm-app/historico/${item.id}`} className="flex items-center gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><BriefcaseBusiness size={22}/></span><div className="min-w-0 flex-1"><strong className="block truncate">{item.cliente} · {item.titulo}</strong><div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-400"><span>{item.etapa}</span><span>{item.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span><span className="inline-flex items-center gap-1"><CalendarDays size={13}/>{dataBR(item.fechamento)}</span></div></div><ChevronRight size={18} className="text-cyan-300"/></Link>)}</div>}
    </div>
  </main>
}

function Kpi({ label, valor }: { label: string; valor: string }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-xs text-slate-400">{label}</p><strong className="mt-1 block text-lg text-cyan-300">{valor}</strong></div> }
