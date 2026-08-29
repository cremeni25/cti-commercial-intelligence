"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { useI18n } from "@/core/i18n"

type Historico={total_clientes?:number;total_estados?:number;total_municipios?:number;metadata?:{total_registros_filtrados?:number}}
type Linhas={metadata?:{descricao?:string};linhas?:Array<{codigo:string;atual:number;anterior:number}>}
const text={
 "pt-BR":{eyebrow:"ANFIR · histórico",title:"Leitura histórica ANFIR",subtitle:"Consulta histórica separada da fotografia estratégica ANFIR 2026. Os filtros de território e período do topo se aplicam somente a esta tela.",context:"Contexto",back:"Voltar ao Dashboard",loading:"Carregando histórico ANFIR...",error:"Não foi possível carregar o histórico ANFIR.",records:"Registros históricos filtrados",clients:"Clientes históricos",states:"Estados atendidos",cities:"Municípios",chart:"Volume ANFIR por linha",fallback:"Período selecionado comparado ao período anterior.",previous:"Período anterior",selected:"Período selecionado"},
 en:{eyebrow:"ANFIR · history",title:"ANFIR historical reading",subtitle:"Historical query separated from the ANFIR 2026 strategic snapshot. The territory and period filters at the top apply only to this screen.",context:"Context",back:"Back to Dashboard",loading:"Loading ANFIR history...",error:"ANFIR history could not be loaded.",records:"Filtered historical records",clients:"Historical clients",states:"States served",cities:"Cities",chart:"ANFIR volume by line",fallback:"Selected period compared with the previous period.",previous:"Previous period",selected:"Selected period"},
 es:{eyebrow:"ANFIR · histórico",title:"Lectura histórica ANFIR",subtitle:"Consulta histórica separada de la fotografía estratégica ANFIR 2026. Los filtros de territorio y período superiores se aplican solamente a esta pantalla.",context:"Contexto",back:"Volver al Dashboard",loading:"Cargando histórico ANFIR...",error:"No fue posible cargar el histórico ANFIR.",records:"Registros históricos filtrados",clients:"Clientes históricos",states:"Estados atendidos",cities:"Municipios",chart:"Volumen ANFIR por línea",fallback:"Período seleccionado comparado con el período anterior.",previous:"Período anterior",selected:"Período seleccionado"},
} as const

export default function AnfirHistoricoPage(){
 const{queryString,contextoAtual}=useOperationalContext();const{locale}=useI18n();const tx=text[locale]
 const[historico,setHistorico]=useState<Historico|null>(null),[linhas,setLinhas]=useState<Linhas|null>(null),[loading,setLoading]=useState(true),[erro,setErro]=useState(false)
 useEffect(()=>{let ativo=true;queueMicrotask(()=>{if(!ativo)return;setLoading(true);setErro(false);Promise.all([
   fetch(`/api/cti/analytics/dashboard?${queryString}`,{cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject()),
   fetch(`/api/cti/analytics/product-lines?${queryString}`,{cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject()),
  ]).then(([h,l])=>{if(ativo){setHistorico(h);setLinhas(l)}}).catch(()=>{if(ativo)setErro(true)}).finally(()=>{if(ativo)setLoading(false)})});return()=>{ativo=false}},[queryString])
 const dados=(linhas?.linhas??[]).map(l=>({linha:l.codigo,anterior:l.anterior,atual:l.atual}))
 return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1 overflow-hidden"><Topbar/><div className="space-y-6 p-4 sm:p-6 lg:p-8">
  <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">{tx.eyebrow}</p><h1 className="mt-2 text-3xl font-bold">{tx.title}</h1><p className="mt-2 max-w-4xl text-sm text-slate-400">{tx.subtitle}</p><p className="mt-2 text-sm text-cyan-300">{tx.context}: {contextoAtual.label}</p></div><Link href="/dashboard" className="inline-flex shrink-0 items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2.5 text-sm font-semibold text-cyan-200">{tx.back}</Link></header>
  {loading&&<div className="rounded-2xl border border-[#17304d] bg-[#071427] p-6 text-sm text-slate-400">{tx.loading}</div>}
  {erro&&<div className="rounded-2xl border border-amber-700/60 bg-amber-950/10 p-6 text-sm text-amber-200">{tx.error}</div>}
  {!loading&&!erro&&<><section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Metric titulo={tx.records} valor={fmt(historico?.metadata?.total_registros_filtrados)}/><Metric titulo={tx.clients} valor={fmt(historico?.total_clientes)}/><Metric titulo={tx.states} valor={fmt(historico?.total_estados)}/><Metric titulo={tx.cities} valor={fmt(historico?.total_municipios)}/></section><section className="rounded-2xl border border-[#17304d] bg-[#071427] p-5"><div className="mb-4"><h2 className="text-lg font-bold">{tx.chart}</h2><p className="mt-1 text-xs text-slate-500">{linhas?.metadata?.descricao||tx.fallback}</p></div><div className="h-[340px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={dados} margin={{top:30,right:18,left:0,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="linha" stroke="#8294ad"/><YAxis stroke="#8294ad"/><Tooltip contentStyle={{backgroundColor:"#061126",border:"1px solid #24507a",borderRadius:"12px",color:"#fff"}}/><Legend/><Bar dataKey="anterior" name={tx.previous} fill="#52657d" radius={[7,7,0,0]}><LabelList dataKey="anterior" position="top" fill="#94a3b8" fontSize={12}/></Bar><Bar dataKey="atual" name={tx.selected} fill="#22d3ee" radius={[7,7,0,0]}><LabelList dataKey="atual" position="top" fill="#67e8f9" fontSize={12}/></Bar></BarChart></ResponsiveContainer></div></section></>}
 </div></section></main>
}
function fmt(v?:number){return Number(v??0).toLocaleString("pt-BR")}
function Metric({titulo,valor}:{titulo:string;valor:string}){return <div className="rounded-xl border border-[#193354] bg-[#08162d] p-4"><p className="text-xs uppercase tracking-wide text-slate-500">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div>}
