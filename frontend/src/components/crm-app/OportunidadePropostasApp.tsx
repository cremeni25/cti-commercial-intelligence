"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { FilePlus2, FileText, Loader2 } from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type Item = { id:string; equipamento:string; quantidade:number; preco_tabela:number; preco_unitario:number; desconto_percentual:number; status:string }
type Proposta = { id:string; numero:string; valor:number; status_documento:string; versao:number }

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function moeda(valor: unknown): string { return Number(valor || 0).toLocaleString("pt-BR", { style:"currency", currency:"BRL" }) }

export default function OportunidadePropostasApp({ oportunidadeId }: { oportunidadeId:string }) {
  const { usuario } = useAuth()
  const [itens,setItens] = useState<Item[]>([])
  const [propostas,setPropostas] = useState<Record<string,Proposta[]>>({})
  const [carregando,setCarregando] = useState(true)
  const [processando,setProcessando] = useState("")
  const [erro,setErro] = useState("")
  const [mensagem,setMensagem] = useState("")

  const carregar = useCallback(async()=>{
    if(!oportunidadeId)return
    setCarregando(true);setErro("")
    try{
      const resposta=await fetch(`/api/crm-proxy/crm-documentos/oportunidades/${encodeURIComponent(oportunidadeId)}/itens`,{cache:"no-store"})
      const payload=await resposta.json().catch(()=>[])
      if(!resposta.ok)throw new Error(texto((payload as Registro).detail)||`Falha ${resposta.status}`)
      const lista=(Array.isArray(payload)?payload:[]).map((item:Registro):Item=>({id:texto(item.id),equipamento:texto(item.nome_comercial||item.equipamento)||"Equipamento",quantidade:Number(item.quantidade||1),preco_tabela:Number(item.preco_tabela||item.preco_unitario||0),preco_unitario:Number(item.preco_unitario||0),desconto_percentual:Number(item.desconto_percentual||0),status:texto(item.status||"EM_NEGOCIACAO")})).filter(item=>item.id)
      setItens(lista)
      const pares=await Promise.all(lista.map(async(item)=>{const r=await fetch(`/api/crm-proxy/crm-documentos/itens/${encodeURIComponent(item.id)}/propostas`,{cache:"no-store"});const p=await r.json().catch(()=>[]);return [item.id,Array.isArray(p)?p:[]] as const}))
      setPropostas(Object.fromEntries(pares))
    }catch(falha){setErro(falha instanceof Error?falha.message:"Não foi possível carregar itens e propostas.")}
    finally{setCarregando(false)}
  },[oportunidadeId])

  useEffect(()=>{queueMicrotask(()=>void carregar())},[carregar])

  async function gerar(item:Item){
    const responsavel=texto(usuario?.id)
    if(!responsavel)return setErro("Não foi possível confirmar o vendedor autenticado.")
    setProcessando(item.id);setErro("");setMensagem("")
    try{
      const resposta=await fetch(`/api/crm-proxy/crm-documentos/itens/${encodeURIComponent(item.id)}/propostas`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({responsavel_id:responsavel})})
      const payload=await resposta.json().catch(()=>({}))
      if(!resposta.ok)throw new Error(texto((payload as Registro).detail)||`Não foi possível gerar a proposta (${resposta.status}).`)
      setMensagem(`Proposta criada para ${item.equipamento}.`)
      await carregar()
    }catch(falha){setErro(falha instanceof Error?falha.message:"Falha ao gerar proposta.")}
    finally{setProcessando("")}
  }

  return <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
    <div className="mb-4 flex items-center gap-2"><FileText className="text-cyan-300"/><div><h2 className="text-lg font-bold">Itens e propostas</h2><p className="text-xs text-slate-400">Preço, desconto e documento comercial da negociação</p></div></div>
    {erro&&<div className="mb-3 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-200">{erro}</div>}
    {mensagem&&<div className="mb-3 rounded-xl border border-emerald-900 bg-emerald-950/30 p-3 text-sm text-emerald-200">{mensagem}</div>}
    {carregando?<div className="grid min-h-28 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>:itens.length===0?<div className="rounded-2xl border border-dashed border-[#24466f] p-4 text-sm text-slate-400">A oportunidade ainda não possui item comercial. Abra a edição da oportunidade para completar produto, preço e desconto.</div>:<div className="space-y-3">{itens.map(item=>{const lista=propostas[item.id]||[],precoNegociado=item.preco_tabela*(1-item.desconto_percentual/100),valorTotal=precoNegociado*item.quantidade,podeGerar=!['ACEITO','CONVERTIDO_PEDIDO','CANCELADO','PERDIDO'].includes(item.status)&&!lista.some(p=>['ACEITA','CONVERTIDA_PEDIDO'].includes(texto(p.status_documento).toUpperCase()));return <article key={item.id} className="rounded-2xl border border-[#24466f] bg-[#091a33] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><strong>{item.equipamento}</strong><p className="mt-1 text-xs text-slate-400">{item.quantidade} un. · tabela {moeda(item.preco_tabela)} · desconto {item.desconto_percentual.toLocaleString('pt-BR',{maximumFractionDigits:2})}%</p><p className="mt-1 text-sm font-semibold text-emerald-300">Negociado: {moeda(valorTotal)}</p></div>{podeGerar&&<button disabled={processando===item.id} onClick={()=>void gerar(item)} className="flex items-center gap-2 rounded-xl bg-cyan-500 px-3 py-2 text-xs font-bold text-slate-950 disabled:opacity-50">{processando===item.id?<Loader2 size={15} className="animate-spin"/>:<FilePlus2 size={15}/>}Gerar proposta</button>}</div>{lista.length>0&&<div className="mt-3 space-y-2 border-t border-[#24466f] pt-3">{lista.map(proposta=><Link key={proposta.id} href={`/crm-app/propostas/${encodeURIComponent(proposta.id)}`} className="flex items-center justify-between gap-3 rounded-xl border border-cyan-900 bg-[#061326] p-3"><span className="min-w-0"><strong className="block truncate text-sm">{texto(proposta.numero)||"Proposta comercial"}</strong><span className="text-xs text-slate-400">{texto(proposta.status_documento)||"RASCUNHO"} · {moeda(proposta.valor)}</span></span><span className="text-xs font-semibold text-cyan-300">Abrir →</span></Link>)}</div>}</article>})}</div>}
  </section>
}