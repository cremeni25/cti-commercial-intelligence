"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import { ArrowLeft, Search } from "lucide-react"
import { useRouter, useSearchParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"

type Detalhe={
 id:string;data:string;cliente?:string;cnpj?:string;cidade?:string;estado?:string;ddd?:string;segmento?:string;
 fabricante?:string|null;fabricante_fonte?:string|null;fabricante_bruto?:string|null;fabricante_cti?:string|null;classificado_cti?:boolean;
 grupo?:string;grupo_fonte?:string;status?:string;motivo?:string;ocorrencia?:string;competencia?:string
}
type Payload={metadata:{fabricantes_ativos:string[];edicao_classificacao_cti?:boolean;regra_edicao?:string};detalhes:Detalhe[]}

async function seguro<T>(url:string,init?:RequestInit):Promise<T>{
 const supabase=getSupabaseClient();const {data,error}=await supabase.auth.getSession();const token=data.session?.access_token
 if(error||!token)throw new Error("Sessão CTI não autenticada.")
 const resposta=await fetch(url,{...init,cache:"no-store",headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json",Accept:"application/json",...(init?.headers||{})}})
 const body=await resposta.json().catch(()=>null)
 if(!resposta.ok)throw new Error(body?.detail||`Falha ${resposta.status}`)
 return body as T
}

export default function Page(){return <Suspense fallback={<Tela mensagem="Carregando inteligência competitiva..."/>}><Conteudo/></Suspense>}

function Tela({mensagem}:{mensagem:string}){return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1"><Topbar/><div className="p-6 text-slate-400">{mensagem}</div></section></main>}

function Conteudo(){
 const router=useRouter(),params=useSearchParams()
 const fabricante=params.get("fabricante")||"",fila=params.get("fila")||"",segmento=params.get("segmento")||"",responsavel=params.get("responsavel_id")||""
 const [dados,setDados]=useState<Payload|null>(null),[erro,setErro]=useState(""),[busca,setBusca]=useState(""),[salvando,setSalvando]=useState("")
 const [mensagem,setMensagem]=useState("")
 const carregar=async()=>{try{setErro("");const qs=responsavel?`?responsavel_id=${encodeURIComponent(responsavel)}`:"";setDados(await seguro<Payload>(`/api/cti/analytics/anfir-competitividade-2026${qs}`))}catch(e){setErro(e instanceof Error?e.message:"Falha ao carregar concorrência.")}}
 useEffect(()=>{void carregar()},[responsavel])
 const registros=useMemo(()=>{
   const termo=busca.trim().toUpperCase()
   return (dados?.detalhes||[]).filter(r=>{
    if(segmento&&r.segmento!==segmento)return false
    if(fabricante&&r.fabricante!==fabricante)return false
    if(fila==="nacional-sem-fabricante"&&r.grupo!=="CONCORRENCIA_NACIONAL_NAO_IDENTIFICADA")return false
    if(fila==="a-identificar"&&r.grupo!=="A_IDENTIFICAR")return false
    if(!termo)return true
    return [r.cliente,r.cnpj,r.cidade,r.fabricante,r.fabricante_bruto,r.status,r.ocorrencia].some(v=>String(v||"").toUpperCase().includes(termo))
   })
 },[dados,fabricante,fila,segmento,busca])
 const titulo=fabricante?`Clientes · ${fabricante}`:fila==="nacional-sem-fabricante"?"Nacional · fabricante a identificar":fila==="a-identificar"?"Registros a identificar":"Inteligência por concorrente"
 async function alterar(r:Detalhe,novo:string){
   setSalvando(r.id);setMensagem("")
   try{await seguro(`/api/cti/analytics/anfir-competitividade-2026/registros/${encodeURIComponent(r.id)}/fabricante`,{method:"PATCH",body:JSON.stringify({fabricante:novo||null})});setMensagem("Classificação CTI atualizada. O dado Carrier/JOV original foi preservado.");await carregar()}
   catch(e){setMensagem(e instanceof Error?e.message:"Não foi possível salvar.")}finally{setSalvando("")}
 }
 return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1 overflow-x-hidden"><Topbar/><div className="space-y-5 p-4 sm:p-6 lg:p-8">
  <header className="flex flex-wrap items-start justify-between gap-4"><div><button onClick={()=>router.back()} className="mb-4 inline-flex items-center gap-2 rounded-xl border border-[#17304d] bg-[#071226] px-4 py-2 text-sm text-cyan-200"><ArrowLeft size={16}/>Voltar ao Dashboard</button><p className="text-xs font-semibold uppercase tracking-[.2em] text-amber-300">Inteligência competitiva ANFIR</p><h1 className="mt-2 text-3xl font-bold">{titulo}</h1><p className="mt-2 max-w-4xl text-sm text-slate-400">Abra o total até o cliente e, quando permitido pela fonte, identifique o fabricante concorrente na camada CTI. A planilha Carrier/JOV permanece imutável.</p></div><div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-right"><p className="text-xs uppercase text-slate-400">Registros do recorte</p><strong className="text-3xl text-amber-200">{registros.length.toLocaleString("pt-BR")}</strong></div></header>
  <div className="relative max-w-2xl"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={17}/><input value={busca} onChange={e=>setBusca(e.target.value)} placeholder="Buscar cliente, CNPJ, cidade ou concorrente..." className="w-full rounded-xl border border-[#17304d] bg-[#071226] py-3 pl-10 pr-3 text-sm outline-none focus:border-cyan-500"/></div>
  {erro&&<div className="rounded-xl border border-red-500/50 bg-red-950/20 p-4 text-red-200">{erro}</div>}{mensagem&&<div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-4 text-cyan-100">{mensagem}</div>}
  {!dados&&!erro&&<div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando registros...</div>}
  {dados&&<section className="overflow-hidden rounded-2xl border border-[#17304d] bg-[#071226]"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-[#08162d] text-left text-xs uppercase text-slate-500"><tr><th className="p-3">Cliente</th><th className="p-3">Segmento</th><th className="p-3">Cidade</th><th className="p-3">Categoria fonte</th><th className="p-3">Fabricante fonte</th><th className="p-3">Classificação CTI</th><th className="p-3 min-w-[260px]">Ação Master</th><th className="p-3">Observação</th></tr></thead><tbody className="divide-y divide-[#13203f]">{registros.map(r=>{
    const status=String(r.status||"").toUpperCase().replaceAll(" ","")
    const editavel=Boolean(dados.metadata.edicao_classificacao_cti)&&!["CARRIER","TK"].includes(status)&&["NACIONAL","USADOCONCORRENTE","","NAOCLASSIFICADO"].includes(status)
    const opcoes=(dados.metadata.fabricantes_ativos||[]).filter(x=>x!=="CARRIER"&&!(status==="NACIONAL"&&x==="THERMOKING"))
    return <tr key={r.id} className="align-top hover:bg-[#08162d]/60"><td className="p-3"><strong className="text-white">{r.cliente||"—"}</strong><div className="mt-1 text-xs text-slate-500">{r.cnpj||"CNPJ não informado"}</div></td><td className="p-3 text-cyan-300">{r.segmento||"—"}</td><td className="p-3">{r.cidade||"—"}{r.estado?`/${r.estado}`:""}</td><td className="p-3"><span className="rounded-lg bg-slate-800 px-2 py-1 text-xs">{r.status||"A identificar"}</span></td><td className="p-3">{r.fabricante_bruto||r.fabricante_fonte||"—"}</td><td className="p-3 font-semibold text-amber-300">{r.fabricante||"Não identificado"}{r.classificado_cti&&<div className="mt-1 text-[10px] uppercase tracking-wide text-cyan-400">Confirmado no CTI</div>}</td><td className="p-3">{editavel?<select disabled={salvando===r.id} value={r.fabricante_cti||""} onChange={e=>void alterar(r,e.target.value)} className="w-full rounded-lg border border-[#24415f] bg-[#08162d] px-3 py-2 text-sm"><option value="">Sem classificação CTI</option>{opcoes.map(x=><option key={x} value={x}>{x}</option>)}</select>:<span className="text-xs text-slate-500">{dados.metadata.edicao_classificacao_cti?"Categoria oficial preservada":"Somente Master pode editar"}</span>}</td><td className="max-w-[420px] whitespace-normal p-3 text-xs leading-5 text-slate-400">{r.ocorrencia||r.motivo||"—"}</td></tr>
   })}{registros.length===0&&<tr><td colSpan={8} className="p-8 text-center text-slate-500">Nenhum registro encontrado neste recorte.</td></tr>}</tbody></table></div></section>}
  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-4 text-xs leading-5 text-violet-100"><strong>Governança:</strong> a edição acima cria apenas uma classificação comercial CTI vinculada ao registro. Status, fabricante e observação originais Carrier/JOV não são alterados.</div>
 </div></section></main>
}
