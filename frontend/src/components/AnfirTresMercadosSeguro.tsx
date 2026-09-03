"use client"

import { useEffect, useMemo, useState } from "react"
import { getSupabaseClient } from "@/core/database/supabase"

type ItemImplementadora = {
  implementadora?: string
  registros?: number
  trailer?: number
  diesel_truck?: number
  direct_drive?: number
  nao_classificado?: number
}
type ItemSegmento = {
  codigo?: string
  segmento?: string
  mercado_total?: number
  mercado_excluido?: number
  mercado_real?: number
}
type MercadoViena = {
  mercado_anfir_total?: number
  mercado_fora_escopo_comercial?: number
  mercado_disputavel_viena?: number
  implementadoras_fora_escopo?: ItemImplementadora[]
  comparativo_segmentos?: ItemSegmento[]
  auditoria?: { fecha_total?: boolean; formula_total?: string }
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
const br=(valor:number)=>valor.toLocaleString("pt-BR")

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
    const segmentos=Array.isArray(m.comparativo_segmentos)?m.comparativo_segmentos.map(x=>({
      codigo:String(x?.codigo||""),
      segmento:String(x?.segmento||""),
      total:numero(x?.mercado_total),
      abatimento:numero(x?.mercado_excluido),
      real:numero(x?.mercado_real),
    })):[]
    const implementadoras=Array.isArray(m.implementadoras_fora_escopo)?m.implementadoras_fora_escopo.map(x=>({
      nome:String(x?.implementadora||""),
      registros:numero(x?.registros),
      trailer:numero(x?.trailer),
      dieselTruck:numero(x?.diesel_truck),
      directDrive:numero(x?.direct_drive),
      naoClassificado:numero(x?.nao_classificado),
    })):[]
    return{total,abatimento,real,segmentos,implementadoras,fecha:m.auditoria?.fecha_total!==false}
  },[data])

  if(falhou)return null
  if(!modelo)return <section className="rounded-2xl border border-[#17304d] bg-[#071427] p-5 text-sm text-slate-400">Carregando base auditável de mercado...</section>

  const porCodigo=Object.fromEntries(modelo.segmentos.map(x=>[x.codigo,x])) as Record<string,{codigo:string;segmento:string;total:number;abatimento:number;real:number}>
  const tr=porCodigo.TR||{codigo:"TR",segmento:"Trailer",total:0,abatimento:0,real:0}
  const dt=porCodigo.DT||{codigo:"DT",segmento:"Diesel Truck",total:0,abatimento:0,real:0}
  const dd=porCodigo.DD||{codigo:"DD",segmento:"Direct Drive",total:0,abatimento:0,real:0}

  return <section className="space-y-5 rounded-3xl border border-cyan-500/30 bg-[#061126] p-5 sm:p-6">
    <div>
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">Base executiva auditável</p>
      <h2 className="mt-2 text-2xl font-bold">Mercado total → empresas retiradas → mercado real Viena</h2>
      <p className="mt-2 text-sm text-slate-400">Uma única conta, com os mesmos registros em todos os blocos. O mercado real é sempre o total ANFIR menos Fibra West, High Flex e Planalto.</p>
    </div>

    <div className="grid gap-4 xl:grid-cols-3">
      <MercadoBloco numeroBloco="1" titulo="Mercado total ANFIR" total={modelo.total} tr={tr.total} dt={dt.total} dd={dd.total} destaque="total" />

      <section className="rounded-2xl border border-amber-500/45 bg-amber-950/10 p-5">
        <p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">2 · Empresas retiradas do mercado</p>
        <p className="mt-2 text-3xl font-bold text-amber-200">{br(modelo.abatimento)}</p>
        <div className="mt-4 overflow-x-auto rounded-xl border border-amber-500/20">
          <table className="min-w-full text-xs">
            <thead className="bg-[#101827] text-left uppercase text-slate-500"><tr><th className="p-2.5">Implementadora</th><th className="p-2.5 text-right">Total</th><th className="p-2.5 text-right">TR</th><th className="p-2.5 text-right">DT</th><th className="p-2.5 text-right">DD</th></tr></thead>
            <tbody>{modelo.implementadoras.map(item=><tr key={item.nome} className="border-t border-amber-500/15"><td className="p-2.5 font-semibold text-amber-100">{item.nome}</td><td className="p-2.5 text-right">{br(item.registros)}</td><td className="p-2.5 text-right">{br(item.trailer)}</td><td className="p-2.5 text-right">{br(item.dieselTruck)}</td><td className="p-2.5 text-right">{br(item.directDrive)}</td></tr>)}</tbody>
            <tfoot><tr className="border-t border-amber-400/40 font-bold text-amber-100"><td className="p-2.5">TOTAL A ABATER</td><td className="p-2.5 text-right">{br(modelo.abatimento)}</td><td className="p-2.5 text-right">{br(tr.abatimento)}</td><td className="p-2.5 text-right">{br(dt.abatimento)}</td><td className="p-2.5 text-right">{br(dd.abatimento)}</td></tr></tfoot>
          </table>
        </div>
      </section>

      <MercadoBloco numeroBloco="3" titulo="Mercado real Viena" total={modelo.real} tr={tr.real} dt={dt.real} dd={dd.real} destaque="real" />
    </div>

    <section className="overflow-hidden rounded-2xl border border-[#17304d] bg-[#071427]">
      <div className="border-b border-[#17304d] px-4 py-3"><h3 className="font-bold">Conciliação auditável</h3><p className="mt-1 text-xs text-slate-500">Cada linha precisa fechar exatamente: Mercado total − Empresas retiradas = Mercado real Viena.</p></div>
      <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-[#0b1b34] text-left text-xs uppercase text-slate-400"><tr><th className="p-3">Leitura</th><th className="p-3 text-right">Mercado total</th><th className="p-3 text-right">Retirar</th><th className="p-3 text-right">Mercado real</th><th className="p-3">Fechamento</th></tr></thead><tbody>
        <LinhaAuditoria nome="TOTAL" total={modelo.total} abater={modelo.abatimento} real={modelo.real}/>
        <LinhaAuditoria nome="Trailer" total={tr.total} abater={tr.abatimento} real={tr.real}/>
        <LinhaAuditoria nome="Diesel Truck" total={dt.total} abater={dt.abatimento} real={dt.real}/>
        <LinhaAuditoria nome="Direct Drive" total={dd.total} abater={dd.abatimento} real={dd.real}/>
      </tbody></table></div>
    </section>

    <div className={`rounded-xl border px-4 py-3 text-sm font-semibold ${modelo.fecha&&modelo.total-modelo.abatimento===modelo.real?"border-emerald-500/30 bg-emerald-500/10 text-emerald-200":"border-red-500/40 bg-red-500/10 text-red-200"}`}>
      {modelo.fecha&&modelo.total-modelo.abatimento===modelo.real?`Fechamento confirmado: ${br(modelo.total)} − ${br(modelo.abatimento)} = ${br(modelo.real)}.`:"Inconsistência detectada: o Dashboard não deve usar este recorte até o fechamento dos números."}
    </div>

    <p className="text-xs text-cyan-200/80">Abaixo desta linha, participação Carrier, concorrência, evolução mensal, DDDs e demais comparativos usam exclusivamente o Mercado real Viena.</p>
  </section>
}

function MercadoBloco({numeroBloco,titulo,total,tr,dt,dd,destaque}:{numeroBloco:string;titulo:string;total:number;tr:number;dt:number;dd:number;destaque:"total"|"real"}){
  const cor=destaque==="real"?"text-emerald-300":"text-cyan-300"
  return <section className="rounded-2xl border border-[#193354] bg-[#08162d] p-5">
    <p className="text-xs font-semibold uppercase tracking-[.16em] text-slate-400">{numeroBloco} · {titulo}</p>
    <p className={`mt-2 text-3xl font-bold ${cor}`}>{br(total)}</p>
    <div className="mt-4 grid grid-cols-3 gap-2">
      <Mini label="Trailer" value={tr}/><Mini label="Diesel Truck" value={dt}/><Mini label="Direct Drive" value={dd}/>
    </div>
  </section>
}

function Mini({label,value}:{label:string;value:number}){
  return <div className="rounded-xl border border-[#193354] bg-[#071427] p-3"><p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 text-lg font-bold text-slate-100">{br(value)}</p></div>
}

function LinhaAuditoria({nome,total,abater,real}:{nome:string;total:number;abater:number;real:number}){
  const fecha=total-abater===real
  return <tr className="border-t border-[#17304d]"><td className="p-3 font-semibold text-slate-200">{nome}</td><td className="p-3 text-right">{br(total)}</td><td className="p-3 text-right text-amber-300">{br(abater)}</td><td className="p-3 text-right font-bold text-emerald-300">{br(real)}</td><td className={`p-3 text-xs font-semibold ${fecha?"text-emerald-300":"text-red-300"}`}>{br(total)} − {br(abater)} = {br(real)} {fecha?"✓":"✕"}</td></tr>
}
