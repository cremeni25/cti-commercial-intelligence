"use client"

import { useEffect, useMemo, useState } from "react"
import { getSupabaseClient } from "@/core/database/supabase"

type ItemImplementadora = { implementadora?: string; registros?: number }
type ItemMensal = { mes?: string; mercado_total?: number; mercado_excluido?: number; mercado_real?: number }
type ItemSegmento = { segmento?: string; mercado_total?: number; mercado_excluido?: number; mercado_real?: number }
type MercadoViena = {
  mercado_anfir_total?: number
  mercado_fora_escopo_comercial?: number
  mercado_disputavel_viena?: number
  implementadoras_fora_escopo?: ItemImplementadora[]
  comparativo_mensal?: ItemMensal[]
  comparativo_segmentos?: ItemSegmento[]
}
type Payload = { mercado_viena?: MercadoViena }

async function buscar(url:string):Promise<Payload>{
  const supabase=getSupabaseClient()
  const {data,error}=await supabase.auth.getSession()
  const token=data.session?.access_token
  if(error||!token)throw new Error("sessao")
  const resposta=await fetch(url,{cache:"no-store",headers:{Authorization:`Bearer ${token}`,Accept:"application/json"}})
  if(!resposta.ok)throw new Error(String(resposta.status))
  return resposta.json() as Promise<Payload>
}

const numero=(valor:unknown)=>Number.isFinite(Number(valor))?Number(valor):0

export default function AnfirTresMercadosSeguro({responsavelId}:{responsavelId?:string}){
  const[data,setData]=useState<Payload|null>(null)
  const[falhou,setFalhou]=useState(false)

  useEffect(()=>{
    let ativo=true
    const qs=responsavelId?`?responsavel_id=${encodeURIComponent(responsavelId)}`:""
    void buscar(`/api/cti/analytics/anfir-workbook-2026${qs}`)
      .then(payload=>{if(ativo){setData(payload);setFalhou(false)}})
      .catch(()=>{if(ativo){setData(null);setFalhou(true)}})
    return()=>{ativo=false}
  },[responsavelId])

  const modelo=useMemo(()=>{
    const m=data?.mercado_viena
    if(!m)return null
    const total=numero(m.mercado_anfir_total)
    const abatimento=numero(m.mercado_fora_escopo_comercial)
    const real=numero(m.mercado_disputavel_viena)
    const mensal=Array.isArray(m.comparativo_mensal)?m.comparativo_mensal.map(x=>({mes:String(x?.mes||""),total:numero(x?.mercado_total),abatimento:numero(x?.mercado_excluido),real:numero(x?.mercado_real)})):[]
    const segmentos=Array.isArray(m.comparativo_segmentos)?m.comparativo_segmentos.map(x=>({segmento:String(x?.segmento||""),total:numero(x?.mercado_total),abatimento:numero(x?.mercado_excluido),real:numero(x?.mercado_real)})):[]
    const implementadoras=Array.isArray(m.implementadoras_fora_escopo)?m.implementadoras_fora_escopo.map(x=>({nome:String(x?.implementadora||""),registros:numero(x?.registros)})):[]
    return{total,abatimento,real,mensal,segmentos,implementadoras}
  },[data])

  if(falhou)return null
  if(!modelo)return <section className="rounded-2xl border border-[#17304d] bg-[#071427] p-5 text-sm text-slate-400">Carregando leitura do mercado real...</section>

  return <section className="space-y-5 rounded-3xl border border-cyan-500/30 bg-[#061126] p-5 sm:p-6">
    <div>
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">Base executiva de mercado</p>
      <h2 className="mt-2 text-2xl font-bold">Mercado total → abatimento → mercado real Viena</h2>
    </div>

    <div className="grid gap-3 lg:grid-cols-3">
      <Bloco titulo="1 · Mercado total ANFIR" valor={modelo.total} detalhe="Fotografia integral do mercado observado." />
      <Bloco titulo="2 · Mercado a abater" valor={modelo.abatimento} detalhe={modelo.implementadoras.map(x=>`${x.nome}: ${x.registros.toLocaleString("pt-BR")}`).join(" · ")||"Fibra West · High Flex · Planalto"} />
      <Bloco titulo="3 · Mercado real Viena" valor={modelo.real} detalhe={`${modelo.total.toLocaleString("pt-BR")} − ${modelo.abatimento.toLocaleString("pt-BR")} = ${modelo.real.toLocaleString("pt-BR")}`} />
    </div>

    {modelo.mensal.length>0&&<GraficoLinha dados={modelo.mensal}/>} 
    {modelo.segmentos.length>0&&<GraficoColunas dados={modelo.segmentos}/>} 

    <p className="text-xs text-cyan-200/80">A partir deste ponto, percentuais, participação Carrier, concorrência e demais comparativos do Dashboard usam somente o Mercado real Viena.</p>
  </section>
}

function Bloco({titulo,valor,detalhe}:{titulo:string;valor:number;detalhe:string}){
  return <div className="rounded-2xl border border-[#193354] bg-[#08162d] p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{titulo}</p><p className="mt-2 text-3xl font-bold text-cyan-300">{valor.toLocaleString("pt-BR")}</p><p className="mt-2 text-xs leading-5 text-slate-500">{detalhe}</p></div>
}

function GraficoLinha({dados}:{dados:Array<{mes:string;total:number;abatimento:number;real:number}>}){
  const max=Math.max(1,...dados.flatMap(d=>[d.total,d.abatimento,d.real]))
  const largura=900,altura=260,padX=44,padY=24
  const x=(i:number)=>dados.length<=1?largura/2:padX+i*((largura-padX*2)/(dados.length-1))
  const y=(v:number)=>altura-padY-(Math.max(0,v)/max)*(altura-padY*2)
  const pontos=(campo:"total"|"abatimento"|"real")=>dados.map((d,i)=>`${x(i)},${y(d[campo])}`).join(" ")
  return <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-5"><h3 className="text-lg font-bold">Evolução mensal · três mercados</h3><div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-400"><span>Mercado total</span><span>Mercado a abater</span><span>Mercado real Viena</span></div><div className="mt-4 overflow-x-auto"><svg viewBox={`0 0 ${largura} ${altura+34}`} className="min-w-[720px] w-full" role="img" aria-label="Evolução mensal dos três mercados"><line x1={padX} y1={altura-padY} x2={largura-padX} y2={altura-padY} stroke="currentColor" className="text-slate-700"/><polyline points={pontos("total")} fill="none" stroke="currentColor" className="text-slate-400" strokeWidth="3"/><polyline points={pontos("abatimento")} fill="none" stroke="currentColor" className="text-amber-400" strokeWidth="3"/><polyline points={pontos("real")} fill="none" stroke="currentColor" className="text-cyan-300" strokeWidth="4"/>{dados.map((d,i)=><g key={`${d.mes}-${i}`}><text x={x(i)} y={altura+16} textAnchor="middle" fill="currentColor" className="text-[10px] text-slate-400">{d.mes.slice(0,3)}</text></g>)}</svg></div></div>
}

function GraficoColunas({dados}:{dados:Array<{segmento:string;total:number;abatimento:number;real:number}>}){
  const max=Math.max(1,...dados.flatMap(d=>[d.total,d.abatimento,d.real]))
  return <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-5"><h3 className="text-lg font-bold">Mercado por linha · três mercados</h3><div className="mt-5 grid gap-5 md:grid-cols-3">{dados.map((d,i)=><div key={`${d.segmento}-${i}`} className="rounded-xl border border-[#17304d] bg-[#08162d] p-4"><p className="text-sm font-semibold text-slate-200">{d.segmento}</p><div className="mt-4 flex h-44 items-end justify-center gap-3"><Coluna valor={d.total} max={max} legenda="Total" classe="bg-slate-500"/><Coluna valor={d.abatimento} max={max} legenda="Abater" classe="bg-amber-400"/><Coluna valor={d.real} max={max} legenda="Real" classe="bg-cyan-400"/></div></div>)}</div></div>
}

function Coluna({valor,max,legenda,classe}:{valor:number;max:number;legenda:string;classe:string}){
  const altura=Math.max(valor>0?8:0,Math.round((valor/max)*120))
  return <div className="flex w-16 flex-col items-center justify-end"><span className="mb-1 text-xs font-semibold text-slate-300">{valor.toLocaleString("pt-BR")}</span><div className={`w-9 rounded-t-md ${classe}`} style={{height:`${altura}px`}}/><span className="mt-2 text-[10px] uppercase tracking-wide text-slate-500">{legenda}</span></div>
}
