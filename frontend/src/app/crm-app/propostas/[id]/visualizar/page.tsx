"use client"

import { useEffect, useState } from "react"
import { ArrowLeft, Loader2 } from "lucide-react"
import { useParams, useRouter } from "next/navigation"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Pagina={numero:number;imagem:string}
type Payload={numero?:string;paginas?:Pagina[];detail?:string}

export default function VisualizarPropostaPage(){
 const params=useParams<{id:string}>(),router=useRouter(),id=String(params.id||"")
 const[paginas,setPaginas]=useState<Pagina[]>([]),[numero,setNumero]=useState(""),[erro,setErro]=useState(""),[carregando,setCarregando]=useState(true)
 useEffect(()=>{let ativo=true;async function carregar(){setCarregando(true);setErro("");try{const r=await fetchCrmSeguroProxy(`crm-app/propostas/${encodeURIComponent(id)}/visualizar-paginas`,{cache:"no-store"}),p=await r.json().catch(()=>({})) as Payload;if(!r.ok)throw new Error(String(p.detail||"Não foi possível visualizar a proposta."));if(ativo){setNumero(String(p.numero||"Proposta"));setPaginas(Array.isArray(p.paginas)?p.paginas:[])}}catch(e){if(ativo)setErro(e instanceof Error?e.message:"Não foi possível visualizar a proposta.")}finally{if(ativo)setCarregando(false)}}if(id)void carregar();return()=>{ativo=false}},[id])
 return <main className="min-h-[100dvh] bg-[#020817] px-3 py-4 text-white sm:px-5"><div className="mx-auto max-w-5xl"><header className="sticky top-0 z-10 mb-4 flex items-center gap-3 border-b border-[#16325c] bg-[#020817]/95 py-3 backdrop-blur"><button type="button" onClick={()=>router.back()} className="grid size-10 place-items-center rounded-xl border border-[#16325c] bg-[#091a33] text-cyan-300" aria-label="Voltar"><ArrowLeft size={18}/></button><div><p className="text-xs uppercase tracking-[0.2em] text-cyan-400">CTI CRM · PDF</p><h1 className="text-lg font-bold">{numero||"Visualizar proposta"}</h1></div></header>{carregando&&<div className="grid min-h-72 place-items-center"><div className="text-center"><Loader2 className="mx-auto mb-3 animate-spin text-cyan-300"/><p className="text-sm text-slate-400">Preparando documento oficial...</p></div></div>}{erro&&<div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}{!carregando&&!erro&&<div className="space-y-4">{paginas.map(p=><section key={p.numero} className="overflow-hidden rounded-xl border border-[#16325c] bg-white shadow-2xl"><img src={p.imagem} alt={`Página ${p.numero} da proposta ${numero}`} className="block h-auto w-full"/></section>)}</div>}</div></main>
}
