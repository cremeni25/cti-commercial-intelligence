"use client"

import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { getSupabaseClient } from "@/core/database/supabase"

type MercadoComparativo = {
  mercado_anfir_total:number
  mercado_fora_escopo_comercial:number
  mercado_disputavel_viena:number
  implementadoras_fora_escopo:Array<{implementadora:string;registros:number}>
  comparativo_mensal:Array<{mes:string;mercado_total:number;mercado_excluido:number;mercado_real:number}>
  comparativo_segmentos:Array<{codigo:string;segmento:string;mercado_total:number;mercado_excluido:number;mercado_real:number}>
}
type Payload={mercado_viena:MercadoComparativo}

async function buscar(url:string){
  const supabase=getSupabaseClient()
  const {data,error}=await supabase.auth.getSession()
  const token=data.session?.access_token
  if(error||!token)throw new Error("Sessão CTI não autenticada.")
  const resposta=await fetch(url,{cache:"no-store",headers:{Authorization:`Bearer ${token}`,Accept:"application/json"}})
  if(!resposta.ok)throw new Error(`Falha ${resposta.status}`)
  return resposta.json() as Promise<Payload>
}

export default function AnfirTresMercados({responsavelId}:{responsavelId?:string}){
  const[data,setData]=useState<Payload|null>(null)
  const[erro,setErro]=useState(false)
  useEffect(()=>{let ativo=true;const qs=responsavelId?`?responsavel_id=${encodeURIComponent(responsavelId)}`:"";void buscar(`/api/cti/analytics/anfir-workbook-2026${qs}`).then(x=>{if(ativo){setData(x);setErro(false)}}).catch(()=>{if(ativo)setErro(true)});return()=>{ativo=false}},[responsavelId])
  if(erro)return null
  if(!data)return <section className="rounded-2xl border border-[#17304d] bg-[#071427] p-5 text-sm text-slate-400">Carregando mercado real Viena...</section>
  const m=data.mercado_viena
  return <section className="space-y-5 rounded-3xl border border-cyan-500/30 bg-[#061126] p-5 sm:p-6">
    <div>
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">Leitura executiva do mercado</p>
      <h2 className="mt-2 text-2xl font-bold">Mercado total → abatimento → mercado real Viena</h2>
    </div>
    <div className="grid gap-3 lg:grid-cols-3">
      <Bloco titulo="1 · Mercado total ANFIR" valor={m.mercado_anfir_total} detalhe="Base integral observada na ANFIR 2026."/>
      <Bloco titulo="2 · Mercado a abater" valor={m.mercado_fora_escopo_comercial} detalhe={m.implementadoras_fora_escopo.map(x=>`${x.implementadora}: ${x.registros}`).join(" · ")}/>
      <Bloco titulo="3 · Mercado real Viena" valor={m.mercado_disputavel_viena} detalhe={`${m.mercado_anfir_total} − ${m.mercado_fora_escopo_comercial} = ${m.mercado_disputavel_viena}`}/>
    </div>
    <div className="grid gap-5 xl:grid-cols-2">
      <Grafico titulo="Evolução mensal · três mercados">
        <LineChart data={m.comparativo_mensal} margin={{top:10,right:18,left:0,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="mes" stroke="#8294ad"/><YAxis stroke="#8294ad"/><Tooltip contentStyle={tooltipStyle}/><Legend/><Line type="monotone" dataKey="mercado_total" name="Mercado total" stroke="#94a3b8" strokeWidth={2}/><Line type="monotone" dataKey="mercado_excluido" name="Mercado a abater" stroke="#f59e0b" strokeWidth={2}/><Line type="monotone" dataKey="mercado_real" name="Mercado real Viena" stroke="#22d3ee" strokeWidth={3}/></LineChart>
      </Grafico>
      <Grafico titulo="Mercado por linha · três mercados">
        <BarChart data={m.comparativo_segmentos} margin={{top:10,right:18,left:0,bottom:0}}><CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="segmento" stroke="#8294ad"/><YAxis stroke="#8294ad"/><Tooltip contentStyle={tooltipStyle}/><Legend/><Bar dataKey="mercado_total" name="Mercado total" fill="#64748b" radius={[6,6,0,0]}/><Bar dataKey="mercado_excluido" name="Mercado a abater" fill="#f59e0b" radius={[6,6,0,0]}/><Bar dataKey="mercado_real" name="Mercado real Viena" fill="#22d3ee" radius={[6,6,0,0]}/></BarChart>
      </Grafico>
    </div>
    <p className="text-xs text-cyan-200/80">Todos os indicadores e comparativos apresentados abaixo desta leitura utilizam somente o Mercado real Viena.</p>
  </section>
}

function Bloco({titulo,valor,detalhe}:{titulo:string;valor:number;detalhe:string}){return <div className="rounded-2xl border border-[#193354] bg-[#08162d] p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{titulo}</p><p className="mt-2 text-3xl font-bold text-cyan-300">{valor.toLocaleString("pt-BR")}</p><p className="mt-2 text-xs leading-5 text-slate-500">{detalhe}</p></div>}
function Grafico({titulo,children}:{titulo:string;children:React.ReactNode}){return <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-5"><h3 className="mb-4 text-lg font-bold">{titulo}</h3><div className="h-[300px]"><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div></div>}
const tooltipStyle={backgroundColor:"#061126",border:"1px solid #24507a",borderRadius:"12px",color:"#fff"}
