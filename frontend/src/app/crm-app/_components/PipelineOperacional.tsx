"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowRight, CalendarDays, CircleAlert, History, Loader2, MessageSquarePlus, RefreshCw, TrendingUp } from "lucide-react"

type Registro = Record<string, unknown>
type Negocio = {
  id: string
  cliente: string
  titulo: string
  etapa: string
  valor: number
  probabilidade: number
  fechamento: string
  atividades: number
  encerrada: boolean
}

const ETAPAS = ["OPORTUNIDADE", "ATIVIDADES", "PROPOSTA", "NEGOCIACAO", "PEDIDO", "GANHO", "PERDIDO"] as const
const FINAIS = new Set(["GANHO", "PERDIDO", "CANCELADO", "FATURADO", "ENCERRADO"])
function texto(valor: unknown): string { return String(valor ?? "").trim() }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const item = payload as Registro
    for (const chave of ["dados", "itens", "oportunidades", "resultado"]) if (Array.isArray(item[chave])) return item[chave] as Registro[]
  }
  return []
}
function etapaEditavel(valor: string): string {
  const etapa = valor.toUpperCase()
  if (etapa === "ATIVIDADE" || etapa === "VISITA") return "ATIVIDADES"
  if (etapa === "ACEITE" || etapa === "DOSSIÊ" || etapa === "DOSSIE" || etapa === "CARRIER" || etapa === "FATURADO") return etapa
  return etapa || "OPORTUNIDADE"
}
function moeda(valor: number): string { return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function dataBR(valor: string): string { if (!valor) return "Sem previsão"; const d = new Date(`${valor.slice(0,10)}T12:00:00`); return Number.isNaN(d.getTime()) ? valor : d.toLocaleDateString("pt-BR") }

export default function PipelineOperacional() {
  const [dados, setDados] = useState<Negocio[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const [movendo, setMovendo] = useState("")
  const [destinos, setDestinos] = useState<Record<string, string>>({})
  const [mostrarEncerrados, setMostrarEncerrados] = useState(false)

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const resposta = await fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" })
      const payload = await resposta.json().catch(() => ([]))
      if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
      const negocios = lista(payload).map((item): Negocio => ({
        id: texto(item.oportunidade_id || item.id),
        cliente: texto(item.cliente_nome) || "Cliente em identificação",
        titulo: texto(item.titulo) || "Negociação comercial",
        etapa: etapaEditavel(texto(item.etapa || item.status_oportunidade || item.status)),
        valor: Number(item.valor || item.valor_estimado || 0),
        probabilidade: Number(item.probabilidade || 0),
        fechamento: texto(item.data_fechamento_prevista).slice(0,10),
        atividades: Number(item.quantidade_atividades || 0),
        encerrada: Boolean(item.encerrada) || FINAIS.has(texto(item.etapa || item.status_oportunidade || item.status).toUpperCase()),
      })).filter((item) => item.id)
      setDados(negocios)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o pipeline.") }
    finally { setCarregando(false) }
  }

  useEffect(() => { void carregar() }, [])

  const visiveis = useMemo(() => dados.filter((item) => mostrarEncerrados || !item.encerrada), [dados, mostrarEncerrados])
  const etapasVisiveis = useMemo(() => {
    const base = [...ETAPAS]
    for (const negocio of visiveis) if (!base.includes(negocio.etapa as typeof ETAPAS[number])) base.push(negocio.etapa as typeof ETAPAS[number])
    return base.filter((etapa) => visiveis.some((item) => item.etapa === etapa))
  }, [visiveis])
  const total = visiveis.reduce((s, i) => s + i.valor, 0)
  const ponderado = visiveis.reduce((s, i) => s + i.valor * (i.probabilidade > 1 ? i.probabilidade / 100 : i.probabilidade), 0)
  const semInteracao = visiveis.filter((i) => i.atividades === 0 && !i.encerrada).length
  const hoje = new Date().toISOString().slice(0,10)
  const vencidos = visiveis.filter((i) => !i.encerrada && i.fechamento && i.fechamento < hoje).length

  async function mover(negocio: Negocio) {
    const destino = destinos[negocio.id] || negocio.etapa
    if (!destino || destino === negocio.etapa) return
    setMovendo(negocio.id); setErro(""); setSucesso("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm/oportunidades/${encodeURIComponent(negocio.id)}`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: destino }),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
      setSucesso(`${negocio.cliente}: etapa atualizada para ${destino.replaceAll("_", " ")}.`)
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível mover a oportunidade.") }
    finally { setMovendo("") }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6">
    <div className="mx-auto max-w-[1500px]">
      <header className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Pipeline comercial</h1><p className="text-sm text-slate-400">Quadro operacional dos mesmos negócios do núcleo CTI</p></div><div className="flex gap-2"><button onClick={() => void carregar()} className="grid size-12 place-items-center rounded-2xl border border-[#24466f] text-cyan-300" aria-label="Atualizar"><RefreshCw size={18}/></button><Link href="/crm-app/forecast" className="flex items-center gap-2 rounded-2xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-200"><TrendingUp size={17}/>Forecast</Link></div></header>
      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}
      <section className="mb-4 grid gap-3 sm:grid-cols-5"><Kpi label="Negócios" valor={String(visiveis.length)}/><Kpi label="Valor total" valor={moeda(total)}/><Kpi label="Ponderado" valor={moeda(ponderado)}/><Kpi label="Sem interação" valor={String(semInteracao)} alerta={semInteracao>0}/><Kpi label="Fechamento vencido" valor={String(vencidos)} alerta={vencidos>0}/></section>
      <label className="mb-4 inline-flex items-center gap-2 rounded-xl border border-[#24466f] bg-[#07162b] px-4 py-3 text-sm text-slate-300"><input type="checkbox" checked={mostrarEncerrados} onChange={(e)=>setMostrarEncerrados(e.target.checked)}/>Mostrar negócios encerrados</label>
      {carregando ? <div className="grid min-h-72 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : etapasVisiveis.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-10 text-center text-slate-400">Nenhum negócio no pipeline.</div> : <div className="overflow-x-auto pb-4"><div className="flex min-w-max gap-4">{etapasVisiveis.map((etapa) => {
        const negocios = visiveis.filter((item) => item.etapa === etapa)
        const valorEtapa = negocios.reduce((s, item) => s + item.valor, 0)
        return <section key={etapa} className="w-[330px] shrink-0 rounded-3xl border border-[#16325c] bg-[#061126] p-3"><header className="mb-3 rounded-2xl bg-[#0a2242] p-4"><div className="flex items-center justify-between"><strong>{etapa.replaceAll("_", " ")}</strong><span className="rounded-full bg-cyan-950/70 px-2 py-1 text-xs text-cyan-200">{negocios.length}</span></div><p className="mt-1 text-xs text-slate-400">{moeda(valorEtapa)}</p></header><div className="space-y-3">{negocios.map((negocio) => {
          const atrasado = Boolean(negocio.fechamento) && negocio.fechamento < hoje && !negocio.encerrada
          return <article key={negocio.id} className="rounded-2xl border border-[#24466f] bg-[#07162b] p-4"><h2 className="font-bold leading-5">{negocio.cliente}</h2><p className="mt-1 text-sm text-slate-300">{negocio.titulo}</p><div className="mt-3 space-y-1 text-xs text-slate-400"><p>{moeda(negocio.valor)} · {Math.round((negocio.probabilidade>1?negocio.probabilidade:negocio.probabilidade*100))}%</p><p className="inline-flex items-center gap-1"><CalendarDays size={13}/>{dataBR(negocio.fechamento)}</p>{negocio.atividades===0 && !negocio.encerrada && <p className="flex items-center gap-1 text-amber-300"><CircleAlert size={13}/>Sem interação registrada</p>}{atrasado && <p className="flex items-center gap-1 text-red-300"><CircleAlert size={13}/>Fechamento previsto vencido</p>}</div><div className="mt-3 grid grid-cols-2 gap-2"><Link href={`/crm-app/historico/${negocio.id}?origem=pipeline`} className="flex items-center justify-center gap-1 rounded-xl border border-[#24466f] py-2 text-xs text-cyan-200"><History size={14}/>Histórico</Link><Link href={`/crm-app/atividades/nova?oportunidade=${negocio.id}&origem=pipeline`} className="flex items-center justify-center gap-1 rounded-xl border border-cyan-800 py-2 text-xs text-cyan-200"><MessageSquarePlus size={14}/>Interação</Link></div>{!negocio.encerrada && <div className="mt-3 rounded-xl border border-[#24466f] p-2"><label className="text-[11px] text-slate-400">Mover para</label><select value={destinos[negocio.id] || negocio.etapa} onChange={(e)=>setDestinos((atual)=>({...atual,[negocio.id]:e.target.value}))} className="mt-1 h-10 w-full rounded-lg bg-[#020817] px-2 text-xs">{ETAPAS.map((item)=><option key={item} value={item}>{item.replaceAll("_"," ")}</option>)}</select><button disabled={movendo===negocio.id || (destinos[negocio.id] || negocio.etapa)===negocio.etapa} onClick={()=>void mover(negocio)} className="mt-2 flex h-9 w-full items-center justify-center gap-1 rounded-lg bg-cyan-500 text-xs font-bold text-slate-950 disabled:opacity-40">{movendo===negocio.id?<Loader2 size={14} className="animate-spin"/>:<ArrowRight size={14}/>}Confirmar etapa</button></div>}</article>
        })}</div></section>
      })}</div></div>}
    </div>
  </main>
}

function Kpi({label,valor,alerta=false}:{label:string;valor:string;alerta?:boolean}) { return <div className={`rounded-2xl border p-4 ${alerta?"border-amber-800 bg-amber-950/20":"border-[#16325c] bg-[#07162b]"}`}><p className="text-xs text-slate-400">{label}</p><strong className={`mt-1 block text-lg ${alerta?"text-amber-300":"text-cyan-300"}`}>{valor}</strong></div> }
