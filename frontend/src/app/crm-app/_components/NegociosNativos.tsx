"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  BriefcaseBusiness,
  CalendarDays,
  FilePenLine,
  FileText,
  History,
  Loader2,
  MessageSquarePlus,
  PackageCheck,
  Search,
  TrendingUp,
} from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import { pertenceAoEscopoDoUsuario } from "@/core/rbac/commercial-scope"

type Registro = Record<string, unknown>
type Negocio = {
  id: string
  responsavelId: string
  cliente: string
  titulo: string
  etapa: string
  valor: number
  probabilidade: number
  fechamento: string
  propostaId: string
  propostaNumero: string
  statusProposta: string
  pedidoId: string
  pedidoNumero: string
}

const finais = new Set(["GANHO", "PERDIDO", "CANCELADO", "FATURADO", "ENCERRADO"])

function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const o = payload as Registro
    for (const k of ["dados", "itens", "oportunidades", "resultado"]) {
      if (Array.isArray(o[k])) return o[k] as Registro[]
    }
  }
  return []
}

function texto(v: unknown) { return String(v || "").trim() }
function dataBR(v: string) {
  if (!v) return "Sem previsão"
  const d = new Date(v)
  return Number.isNaN(d.getTime()) ? v : d.toLocaleDateString("pt-BR")
}

function proximoPasso(negocio: Negocio) {
  if (negocio.pedidoId) {
    return negocio.pedidoNumero
      ? `Pedido ${negocio.pedidoNumero} já gerado. Acompanhe a execução pelo pedido.`
      : "Pedido já gerado. Acompanhe a execução pelo pedido."
  }
  if (!negocio.propostaId) return "Próximo passo: abra o negócio e prepare a proposta quando a negociação estiver pronta."
  const status = negocio.statusProposta.toUpperCase().replaceAll(" ", "_")
  if (["ACEITA", "APROVADA"].includes(status)) return "Proposta aceita. Próximo passo: abrir a proposta e converter em pedido."
  if (status === "CONVERTIDA_PEDIDO") return "A proposta já foi convertida em pedido."
  if (["EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)) return "Próximo passo: abrir a proposta, registrar o aceite do cliente e então converter em pedido."
  return "Proposta existente. Abra a proposta para revisar, emitir ou enviar antes do aceite."
}

export default function NegociosNativos({ modo }: { modo: "oportunidades" | "pipeline" }) {
  const { usuario } = useAuth()
  const [dados, setDados] = useState<Negocio[]>([])
  const [busca, setBusca] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" })
      .then(async (r) => {
        const p = await r.json().catch(() => ({}))
        if (!r.ok) throw new Error(String((p as Registro).detail || `Falha ${r.status}`))
        setDados(lista(p).map((i) => ({
          id: texto(i.oportunidade_id || i.id),
          responsavelId: texto(i.responsavel_id),
          cliente: texto(i.cliente_nome || i.razao_social || i.cliente) || "Cliente em identificação",
          titulo: texto(i.titulo || i.equipamento) || "Negociação comercial",
          etapa: texto(i.etapa || i.status_oportunidade || i.status).toUpperCase() || "OPORTUNIDADE",
          valor: Number(i.valor || i.valor_estimado || 0),
          probabilidade: Number(i.probabilidade || i.probabilidade_fechamento || 0),
          fechamento: texto(i.data_fechamento_prevista || i.fechamento_previsto),
          propostaId: texto(i.proposta_id),
          propostaNumero: texto(i.proposta_numero),
          statusProposta: texto(i.status_proposta),
          pedidoId: texto(i.pedido_id),
          pedidoNumero: texto(i.pedido_numero),
        })).filter((i) => i.id))
      })
      .catch((e) => setErro(e instanceof Error ? e.message : "Não foi possível carregar os negócios."))
      .finally(() => setCarregando(false))
  }, [])

  const visiveis = useMemo(() => {
    const escopados = dados.filter((i) => pertenceAoEscopoDoUsuario(i.responsavelId, usuario))
    const base = modo === "oportunidades" ? escopados.filter((i) => !finais.has(i.etapa)) : escopados
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    return termo
      ? base.filter((i) => `${i.cliente} ${i.titulo} ${i.etapa} ${i.propostaNumero} ${i.pedidoNumero}`.toLocaleLowerCase("pt-BR").includes(termo))
      : base
  }, [busca, dados, modo, usuario])

  const total = visiveis.reduce((s, i) => s + i.valor, 0)
  const ponderado = visiveis.reduce((s, i) => s + i.valor * (i.probabilidade > 1 ? i.probabilidade / 100 : i.probabilidade), 0)
  const titulo = modo === "pipeline" ? "Pipeline comercial" : "Oportunidades"
  const origem = modo === "pipeline" ? "pipeline" : "oportunidades"
  const descricao = modo === "pipeline"
    ? "Posição por etapa dos mesmos negócios. Use o Forecast para enxergar a projeção por competência."
    : "Negócios abertos com o próximo passo comercial visível: interação, proposta, aceite e pedido."
  const etapas = useMemo(
    () => Array.from(new Set(visiveis.map((i) => i.etapa))).map((etapa) => ({ etapa, total: visiveis.filter((i) => i.etapa === etapa).length })),
    [visiveis],
  )

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-5xl">
    <header className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">{titulo}</h1><p className="max-w-2xl text-sm text-slate-400">{descricao}</p></div></div>
      {modo === "pipeline" && <Link href="/crm-app/forecast" className="flex items-center justify-center gap-2 rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-200"><TrendingUp size={17}/>Abrir Forecast</Link>}
    </header>

    <div className="mb-4 grid gap-3 sm:grid-cols-3">
      <Kpi label={modo === "pipeline" ? "Negócios no pipeline" : "Oportunidades abertas"} valor={String(visiveis.length)}/>
      <Kpi label="Valor total" valor={total.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}/>
      <Kpi label="Valor ponderado" valor={ponderado.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}/>
    </div>

    {modo === "pipeline" && etapas.length > 0 && <section className="mb-4 rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">Distribuição por etapa</p><div className="mt-3 flex flex-wrap gap-2">{etapas.map((item) => <span key={item.etapa} className="rounded-full border border-[#24466f] bg-[#020817] px-3 py-2 text-xs text-slate-300">{item.etapa.replaceAll("_", " ")} <strong className="ml-1 text-cyan-300">{item.total}</strong></span>)}</div></section>}

    <div className="relative mb-4"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, equipamento, proposta, pedido ou etapa" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></div>

    {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : visiveis.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum negócio encontrado nesta visão.</div> : <div className="space-y-3">{visiveis.map((i) => <article key={i.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4">
      <div className="flex items-start gap-4"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><BriefcaseBusiness size={22}/></span><div className="min-w-0 flex-1"><strong className="block">{i.cliente} · {i.titulo}</strong><div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-400"><span>{i.etapa}</span><span>{i.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span><span className="inline-flex items-center gap-1"><CalendarDays size={13}/>{dataBR(i.fechamento)}</span>{i.propostaNumero && <span className="rounded-full border border-cyan-900 px-2 py-0.5 text-cyan-300">{i.propostaNumero} · {i.statusProposta || "PROPOSTA"}</span>}{i.pedidoNumero && <span className="rounded-full border border-emerald-900 px-2 py-0.5 text-emerald-300">{i.pedidoNumero}</span>}</div></div></div>
      <div className="mt-4 rounded-2xl border border-[#24466f] bg-[#020817]/60 px-4 py-3 text-sm text-slate-300"><strong className="text-cyan-300">Próximo passo: </strong>{proximoPasso(i).replace(/^Próximo passo:\s*/i, "")}</div>
      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        <Link href={`/crm-app/historico/${i.id}?origem=${origem}#timeline`} className="flex items-center justify-center gap-2 rounded-xl border border-cyan-800 px-3 py-3 text-sm font-semibold text-cyan-200"><History size={16}/>Histórico</Link>
        {i.pedidoId ? <Link href={`/crm-app/pedidos/${encodeURIComponent(i.pedidoId)}`} className="flex items-center justify-center gap-2 rounded-xl border border-emerald-700 px-3 py-3 text-sm font-semibold text-emerald-300"><PackageCheck size={16}/>Abrir pedido</Link> : i.propostaId ? <Link href={`/crm-app/propostas/${encodeURIComponent(i.propostaId)}`} className="flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-3 py-3 text-sm font-bold text-white"><FileText size={16}/>Abrir proposta</Link> : <Link href={`/crm-app/historico/${i.id}?origem=${origem}#negociacao`} className="flex items-center justify-center gap-2 rounded-xl border border-[#24466f] px-3 py-3 text-sm font-semibold"><FilePenLine size={16}/>Abrir negócio</Link>}
        <Link href={`/crm-app/atividades/nova?oportunidade=${i.id}&origem=${origem}`} className="flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-3 py-3 text-sm font-bold text-slate-950"><MessageSquarePlus size={16}/>Nova interação</Link>
      </div>
    </article>)}</div>}
  </div></main>
}

function Kpi({ label, valor }: { label: string; valor: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-xs text-slate-400">{label}</p><strong className="mt-1 block text-lg text-cyan-300">{valor}</strong></div>
}
