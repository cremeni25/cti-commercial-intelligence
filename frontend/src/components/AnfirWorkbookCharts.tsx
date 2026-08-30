"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

type WorkbookPayload={inteligencia_viena:{mensal:Array<{mes:string;trailer:number;diesel_truck:number;direct_drive:number;total:number}>;segmentos:Array<{segmento:string;mercado:number;carrier:number;carrier_percentual_observado:number}>}}
type Competidor={fabricante:string;registros:number;percentual_mercado:number}
type CompetitivoSegmento={codigo:string;segmento:string;mercado:number;carrier:number;carrier_percentual:number;concorrencia:number;concorrencia_percentual:number;reaproveitamento_documentacao:number;a_identificar:number;fabricantes_concorrentes:Competidor[];mensal:Array<{mes:string;competencia:string;carrier:number;concorrencia:number;reaproveitamento:number;a_identificar:number;mercado:number}>}
type CompetitivoPayload={metadata:{regra_documentacao:string};resumo:{mercado:number;carrier:number;carrier_percentual:number;concorrencia_identificada:number;concorrencia_percentual:number;reaproveitamento_documentacao:number;a_identificar:number};ranking_concorrentes:Competidor[];segmentos:CompetitivoSegmento[];leituras_estrategicas:string[]}

function drill(titulo:string,campo?:string,valor?:string){
 const q=new URLSearchParams({camada:"anfir",contexto:"viena-sp",periodo:"PERSONALIZADO",inicio:"2026-01-01",fim:"2026-12-31",titulo,subtitulo:"Registros individualizados que compõem a fotografia ANFIR 2026."})
 if(campo)q.set("campo",campo)
 if(valor)q.set("valor",valor)
 return `/detalhamento?${q.toString()}`
}

export default function AnfirWorkbookCharts({responsavelId}:{responsavelId?:string}){
 const[data,setData]=useState<WorkbookPayload|null>(null)
 const[competitivo,setCompetitivo]=useState<CompetitivoPayload|null>(null)
 useEffect(()=>{
   let active=true
   const qs=responsavelId?`?responsavel_id=${encodeURIComponent(responsavelId)}`:""
   Promise.all([
     fetch(`/api/cti/analytics/anfir-workbook-2026${qs}`,{cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject()),
     fetch(`/api/cti/analytics/anfir-competitividade-2026${qs}`,{cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject()),
   ]).then(([workbook,comp])=>{if(active){setData(workbook);setCompetitivo(comp)}}).catch(()=>{})
   return()=>{active=false}
 },[responsavelId])
 if(!data)return null
 const mensal=data.inteligencia_viena.mensal,segmentos=data.inteligencia_viena.segmentos
 return <div className="space-y-5">
  <section className="grid gap-5 xl:grid-cols-2">
   <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-5">
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-400">Auditoria ANFIR 2026</p><h3 className="mt-1 text-lg font-bold">Evolução mensal por linha</h3><p className="mt-1 text-xs text-slate-500">TR, DT e DD dentro da fotografia Viena 2026.</p></div><Link href={drill("Evolução mensal · ANFIR 2026")} className="rounded-lg border border-cyan-600/50 bg-cyan-500/10 px-3 py-2 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-500/20">Abrir registros</Link></div>
    <div className="h-[300px]"><ResponsiveContainer width="100%" height="100%"><LineChart data={mensal} margin={{top:10,right:18,left:0,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="mes" stroke="#8294ad"/><YAxis stroke="#8294ad"/><Tooltip contentStyle={tooltipStyle}/><Legend/><Line type="monotone" dataKey="trailer" name="Trailer" stroke="#22d3ee" strokeWidth={2}/><Line type="monotone" dataKey="diesel_truck" name="Diesel Truck" stroke="#f59e0b" strokeWidth={2}/><Line type="monotone" dataKey="direct_drive" name="Direct Drive" stroke="#34d399" strokeWidth={2}/></LineChart></ResponsiveContainer></div>
   </div>
   <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-5">
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-400">Auditoria ANFIR 2026</p><h3 className="mt-1 text-lg font-bold">Mercado real × Carrier observada</h3><p className="mt-1 text-xs text-slate-500">Tamanho real de cada linha comparado à presença Carrier observada na ANFIR.</p></div><div className="flex flex-wrap gap-2"><Link href={drill("Mercado real · ANFIR 2026")} className="rounded-lg border border-slate-600 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:border-cyan-600 hover:text-cyan-200">Abrir mercado</Link><Link href={drill("Carrier observada · ANFIR 2026","categoria","CARRIER")} className="rounded-lg border border-cyan-600/50 bg-cyan-500/10 px-3 py-2 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-500/20">Abrir Carrier</Link></div></div>
    <div className="h-[300px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={segmentos} margin={{top:10,right:18,left:0,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="segmento" stroke="#8294ad"/><YAxis stroke="#8294ad"/><Tooltip contentStyle={tooltipStyle}/><Legend/><Bar dataKey="mercado" name="Mercado" fill="#64748b" radius={[6,6,0,0]}/><Bar dataKey="carrier" name="Carrier observada" fill="#22d3ee" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></div>
   </div>
  </section>
  {competitivo&&<CompetitiveSection data={competitivo}/>} 
 </div>
}

function CompetitiveSection({data}:{data:CompetitivoPayload}){
 const r=data.resumo
 return <section className="rounded-3xl border border-amber-500/30 bg-[#071427] p-5 sm:p-6">
  <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[.18em] text-amber-300">Inteligência competitiva ANFIR</p><h2 className="mt-2 text-2xl font-bold">Carrier × concorrência por fabricante</h2><p className="mt-2 max-w-4xl text-sm text-slate-400">Fabricantes são normalizados pela taxonomia oficial do CTI. Thermo King deixa de ser coluna fixa e passa a compor a concorrência ao lado dos demais fabricantes identificados.</p></div><Link href="/dashboard/anfir-competitividade-relatorio" className="rounded-xl border border-amber-500/50 bg-amber-500/10 px-4 py-2 text-sm font-semibold text-amber-200 hover:bg-amber-500/20">Relatório competitivo / PDF</Link></div>
  <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
   <Kpi label="Mercado" value={r.mercado}/><Kpi label="Carrier" value={`${r.carrier} · ${r.carrier_percentual.toFixed(1)}%`}/><Kpi label="Concorrência identificada" value={`${r.concorrencia_identificada} · ${r.concorrencia_percentual.toFixed(1)}%`}/><Kpi label="Reaproveitamento / documentação" value={r.reaproveitamento_documentacao}/><Kpi label="Fabricante a identificar" value={r.a_identificar}/><Kpi label="Concorrentes ativos" value={data.ranking_concorrentes.length}/>
  </div>
  <div className="mt-5 overflow-x-auto rounded-2xl border border-[#17304d]"><table className="min-w-full text-sm"><thead className="bg-[#0b1b34] text-left text-xs uppercase text-slate-400"><tr><th className="p-3">Segmento</th><th className="p-3">Mercado</th><th className="p-3">Carrier</th><th className="p-3">Carrier %</th><th className="p-3">Concorrência</th><th className="p-3">Concorrência %</th><th className="p-3">Reaproveitamento</th><th className="p-3">A identificar</th></tr></thead><tbody>{data.segmentos.map(s=><tr key={s.codigo} className="border-t border-[#17304d]"><td className="p-3 font-semibold text-cyan-300">{s.segmento}</td><td className="p-3">{s.mercado}</td><td className="p-3">{s.carrier}</td><td className="p-3">{s.carrier_percentual.toFixed(1)}%</td><td className="p-3 text-amber-300">{s.concorrencia}</td><td className="p-3">{s.concorrencia_percentual.toFixed(1)}%</td><td className="p-3">{s.reaproveitamento_documentacao}</td><td className="p-3">{s.a_identificar}</td></tr>)}</tbody></table></div>
  <div className="mt-5 grid gap-5 xl:grid-cols-3">{data.segmentos.map(s=><div key={s.codigo} className="rounded-2xl border border-[#17304d] bg-[#061126] p-4"><h3 className="font-bold">{s.segmento} · Carrier × concorrência</h3><p className="mt-1 text-xs text-slate-500">Evolução mensal de fabricantes efetivamente identificados.</p><div className="mt-3 h-[260px]"><ResponsiveContainer width="100%" height="100%"><LineChart data={s.mensal} margin={{top:8,right:12,left:-10,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="mes" stroke="#8294ad" tick={{fontSize:11}}/><YAxis stroke="#8294ad"/><Tooltip contentStyle={tooltipStyle}/><Legend/><Line type="monotone" dataKey="carrier" name="Carrier" stroke="#22d3ee" strokeWidth={2.5}/><Line type="monotone" dataKey="concorrencia" name="Concorrência" stroke="#f59e0b" strokeWidth={2.5}/></LineChart></ResponsiveContainer></div></div>)}</div>
  <div className="mt-5 grid gap-5 xl:grid-cols-2"><div className="rounded-2xl border border-[#17304d] bg-[#061126] p-4"><h3 className="font-bold">Ranking de fabricantes concorrentes</h3><div className="mt-3 space-y-2">{data.ranking_concorrentes.length?data.ranking_concorrentes.map((item,i)=><div key={item.fabricante} className="flex items-center justify-between gap-3 rounded-xl bg-[#0a1930] px-3 py-2 text-sm"><span><strong className="mr-2 text-slate-500">{i+1}.</strong>{item.fabricante}</span><span className="text-amber-300">{item.registros} · {item.percentual_mercado.toFixed(1)}%</span></div>):<p className="text-sm text-slate-500">Sem fabricante concorrente identificado no escopo atual.</p>}</div></div><div className="rounded-2xl border border-[#17304d] bg-[#061126] p-4"><h3 className="font-bold">Leitura estratégica</h3><ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">{data.leituras_estrategicas.map(x=><li key={x}>• {x}</li>)}</ul><p className="mt-4 rounded-xl border border-violet-500/30 bg-violet-500/10 p-3 text-xs leading-5 text-violet-100"><strong>Documentação:</strong> {data.metadata.regra_documentacao}</p></div></div>
 </section>
}
function Kpi({label,value}:{label:string;value:string|number}){return <div className="rounded-xl border border-[#193354] bg-[#08162d] p-4"><p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 text-lg font-bold text-cyan-200">{value}</p></div>}
const tooltipStyle={backgroundColor:"#061126",border:"1px solid #24507a",borderRadius:"12px",color:"#fff"}
