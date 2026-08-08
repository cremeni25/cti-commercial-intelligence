"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, CircleDollarSign, Loader2, Search } from "lucide-react"
import JornadaDocumentalNav from "@/components/crm-app/JornadaDocumentalNav"

type Venda = { id?: string; cliente_nome?: string; pedido_numero?: string; equipamento_nome?: string; equipamento_codigo?: string; tipo_venda?: string; valor?: number; data_venda?: string }
function moeda(valor: unknown){return Number(valor||0).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}
function dataBr(valor?: string){if(!valor)return "—";const d=new Date(`${valor}T12:00:00`);return Number.isNaN(d.getTime())?valor:d.toLocaleDateString("pt-BR")}

export default function VendasCrmAppPage(){
  const [dados,setDados]=useState<Venda[]>([]),[busca,setBusca]=useState(""),[carregando,setCarregando]=useState(true),[erro,setErro]=useState("")
  useEffect(()=>{fetch("/api/crm-proxy/vendas",{cache:"no-store"}).then(async r=>{const p=await r.json().catch(()=>[]);if(!r.ok)throw new Error(String(p.detail||`Falha ${r.status}`));setDados(Array.isArray(p)?p:[])}).catch(f=>setErro(f instanceof Error?f.message:"Não foi possível carregar as vendas.")).finally(()=>setCarregando(false))},[])
  const filtrados=useMemo(()=>{const termo=busca.trim().toLocaleLowerCase("pt-BR");if(!termo)return dados;return dados.filter(i=>`${i.cliente_nome||""} ${i.pedido_numero||""} ${i.equipamento_nome||i.equipamento_codigo||""} ${i.tipo_venda||""}`.toLocaleLowerCase("pt-BR").includes(termo))},[busca,dados])
  const valorTotal=dados.reduce((t,i)=>t+Number(i.valor||0),0)
  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-6xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Vendas realizadas</h1><p className="text-sm text-slate-400">Histórico dos negócios concluídos no CRM App</p></div></header>
    <JornadaDocumentalNav/>
    <section className="mb-4 grid grid-cols-2 gap-3"><div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><p className="text-xs uppercase tracking-[.12em] text-slate-500">Vendas registradas</p><strong className="mt-2 block text-2xl text-cyan-300">{dados.length}</strong></div><div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><p className="text-xs uppercase tracking-[.12em] text-slate-500">Valor realizado</p><strong className="mt-2 block text-2xl text-emerald-300">{moeda(valorTotal)}</strong></div></section>
    <label className="relative mb-4 block"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={e=>setBusca(e.target.value)} placeholder="Buscar cliente, pedido, equipamento ou tipo" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></label>
    {erro&&<div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {carregando?<div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>:filtrados.length===0?<div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhuma venda encontrada.</div>:<div className="space-y-3">{filtrados.map((item,index)=><div key={item.id||index} className="flex items-center gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><span className="rounded-2xl bg-emerald-950/40 p-3 text-emerald-300"><CircleDollarSign size={22}/></span><span className="min-w-0 flex-1"><strong className="block truncate text-lg">{item.cliente_nome||"Cliente não identificado"}</strong><span className="mt-1 block text-sm text-slate-300">{item.equipamento_nome||item.equipamento_codigo||"Equipamento a definir"}</span><span className="mt-2 block text-xs text-slate-500">{dataBr(item.data_venda)} · {item.tipo_venda||"VENDA"} · {moeda(item.valor)}</span><span className="mt-1 block text-[11px] text-slate-600">Pedido {item.pedido_numero||"—"}</span></span></div>)}</div>}
  </div></main>
}
