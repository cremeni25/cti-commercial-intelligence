"use client"

import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

type Payload={inteligencia_viena:{mensal:Array<{mes:string;trailer:number;diesel_truck:number;direct_drive:number;total:number}>;segmentos:Array<{segmento:string;mercado:number;carrier:number;carrier_percentual_observado:number}>}}

export default function AnfirWorkbookCharts(){
 const[data,setData]=useState<Payload|null>(null)
 useEffect(()=>{let active=true;fetch("/api/cti/analytics/anfir-workbook-2026",{cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject()).then(p=>{if(active)setData(p)}).catch(()=>{});return()=>{active=false}},[])
 if(!data)return null
 const mensal=data.inteligencia_viena.mensal
 const segmentos=data.inteligencia_viena.segmentos
 return <section className="grid gap-5 xl:grid-cols-2">
  <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-5">
   <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-400">Auditoria ANFIR 2026</p><h3 className="mt-1 text-lg font-bold">Evolução mensal por linha</h3><p className="mt-1 text-xs text-slate-500">Mesma leitura da planilha auditada: TR, DT e DD dentro da fotografia Viena 2026.</p></div>
   <div className="h-[300px]"><ResponsiveContainer width="100%" height="100%"><LineChart data={mensal} margin={{top:10,right:18,left:0,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="mes" stroke="#8294ad"/><YAxis stroke="#8294ad"/><Tooltip contentStyle={tooltipStyle}/><Legend/><Line type="monotone" dataKey="trailer" name="Trailer" stroke="#22d3ee" strokeWidth={2}/><Line type="monotone" dataKey="diesel_truck" name="Diesel Truck" stroke="#f59e0b" strokeWidth={2}/><Line type="monotone" dataKey="direct_drive" name="Direct Drive" stroke="#34d399" strokeWidth={2}/></LineChart></ResponsiveContainer></div>
  </div>
  <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-5">
   <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-400">Auditoria ANFIR 2026</p><h3 className="mt-1 text-lg font-bold">Mercado real × Carrier observada</h3><p className="mt-1 text-xs text-slate-500">Compara o tamanho real de cada linha com a presença Carrier observada na ANFIR.</p></div>
   <div className="h-[300px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={segmentos} margin={{top:10,right:18,left:0,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="segmento" stroke="#8294ad"/><YAxis stroke="#8294ad"/><Tooltip contentStyle={tooltipStyle}/><Legend/><Bar dataKey="mercado" name="Mercado" fill="#64748b" radius={[6,6,0,0]}/><Bar dataKey="carrier" name="Carrier observada" fill="#22d3ee" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></div>
  </div>
 </section>
}

const tooltipStyle={backgroundColor:"#061126",border:"1px solid #24507a",borderRadius:"12px",color:"#fff"}
