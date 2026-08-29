"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import JornadaComercialNav from "@/components/crm/JornadaComercialNav"
import { useAuth } from "@/core/auth/AuthContext"
import { useOperationalI18n } from "@/core/i18n/operational"
import { pertenceAoEscopoDoUsuario, possuiEscopoProprio } from "@/core/rbac/commercial-scope"
import { API_URL } from "@/lib/api"

type Snapshot = { validade?: string | null; oportunidade?: { titulo?: string; cliente_nome?: string; empresa_nome?: string } }
type Proposta = { id: string; numero?: string; cliente_id?: string; oportunidade_id?: string; item_oportunidade_id?: string; valor?: number; status?: string; status_documento?: string; validade?: string; versao?: number; created_at?: string; snapshot_dados?: Snapshot }
type LinhaNucleo = { oportunidade_id?: string; proposta_id?: string; proposta_vigente_id?: string; cliente_nome?: string; titulo?: string; responsavel_id?:string|null }
type Grupo = { chave: string; proposta: Proposta; versoes: Proposta[]; cliente: string; oportunidade: string; validade: string }
type FiltroProposta = "TODOS" | "ACEITAS_CONVERTIDAS" | "ELABORACAO" | "EMITIDA" | "ENVIADA" | "EM_NEGOCIACAO" | "ACEITA" | "CONVERTIDA_PEDIDO" | "CANCELADA"

const textos = {
  "pt-BR": {
    subtitle:"Documento comercial da negociação: versão, emissão, aceite e conversão. O negócio continua sendo a mesma oportunidade.", dealsWithProposal:"Negociações com proposta", consolidatedValue:"Valor comercial consolidado", acceptedConverted:"Aceitas / convertidas", status:"Status", all:"Todos", title:"Propostas comerciais", explanation:"Aqui se administra o documento; pedido e venda aparecem nas etapas seguintes da mesma jornada.", currentFilter:"Filtro atual", loading:"Carregando...", client:"Cliente", currentProposal:"Proposta vigente", opportunity:"Oportunidade", value:"Valor", validity:"Validade", versions:"Versões", action:"Ação", noNumber:"Proposta sem número", data:"Dados", view:"Visualizar proposta", unidentifiedClient:"Cliente não identificado", genericOpportunity:"Oportunidade comercial", notProvided:"Não informada", click:"Clique para detalhar",
    statuses:{ RASCUNHO:"Em elaboração", ELABORACAO:"Em elaboração", EM_REVISAO:"Em revisão", APROVADA_INTERNA:"Aprovada internamente", EMITIDA:"Emitida", ENVIADA:"Enviada", VISUALIZADA:"Visualizada", EM_NEGOCIACAO:"Em negociação", APROVADA:"Aceita", ACEITA:"Aceita", CONVERTIDA_PEDIDO:"Convertida em pedido", SUBSTITUIDA:"Substituída", REJEITADA:"Rejeitada", EXPIRADA:"Expirada", CANCELADA:"Cancelada" }
  },
  en: {
    subtitle:"Commercial document for the deal: versioning, issuance, acceptance and conversion. The underlying deal remains the same opportunity.", dealsWithProposal:"Deals with proposals", consolidatedValue:"Consolidated proposal value", acceptedConverted:"Accepted / converted", status:"Status", all:"All", title:"Sales proposals", explanation:"This view manages the commercial document; order and sale appear in the next stages of the same journey.", currentFilter:"Current filter", loading:"Loading...", client:"Account", currentProposal:"Current proposal", opportunity:"Opportunity", value:"Value", validity:"Valid until", versions:"Versions", action:"Action", noNumber:"Proposal without number", data:"Details", view:"View proposal", unidentifiedClient:"Account not identified", genericOpportunity:"Commercial opportunity", notProvided:"Not provided", click:"Click to view details",
    statuses:{ RASCUNHO:"Draft", ELABORACAO:"Draft", EM_REVISAO:"Under review", APROVADA_INTERNA:"Internally approved", EMITIDA:"Issued", ENVIADA:"Sent", VISUALIZADA:"Viewed", EM_NEGOCIACAO:"In negotiation", APROVADA:"Accepted", ACEITA:"Accepted", CONVERTIDA_PEDIDO:"Converted to order", SUBSTITUIDA:"Superseded", REJEITADA:"Rejected", EXPIRADA:"Expired", CANCELADA:"Cancelled" }
  },
  es: {
    subtitle:"Documento comercial de la negociación: versión, emisión, aceptación y conversión. El negocio continúa siendo la misma oportunidad.", dealsWithProposal:"Negocios con propuesta", consolidatedValue:"Valor comercial consolidado", acceptedConverted:"Aceptadas / convertidas", status:"Estado", all:"Todos", title:"Propuestas comerciales", explanation:"Aquí se administra el documento; el pedido y la venta aparecen en las siguientes etapas de la misma jornada.", currentFilter:"Filtro actual", loading:"Cargando...", client:"Cliente", currentProposal:"Propuesta vigente", opportunity:"Oportunidad", value:"Valor", validity:"Vigencia", versions:"Versiones", action:"Acción", noNumber:"Propuesta sin número", data:"Datos", view:"Ver propuesta", unidentifiedClient:"Cliente no identificado", genericOpportunity:"Oportunidad comercial", notProvided:"No informado", click:"Haga clic para ver detalles",
    statuses:{ RASCUNHO:"En elaboración", ELABORACAO:"En elaboración", EM_REVISAO:"En revisión", APROVADA_INTERNA:"Aprobada internamente", EMITIDA:"Emitida", ENVIADA:"Enviada", VISUALIZADA:"Visualizada", EM_NEGOCIACAO:"En negociación", APROVADA:"Aceptada", ACEITA:"Aceptada", CONVERTIDA_PEDIDO:"Convertida en pedido", SUBSTITUIDA:"Sustituida", REJEITADA:"Rechazada", EXPIRADA:"Vencida", CANCELADA:"Cancelada" }
  }
} as const

function statusCodigo(item: Proposta) { return String(item.status_documento || item.status || "RASCUNHO").toUpperCase() }
function aceitaOuConvertida(item: Proposta){return ["ACEITA","CONVERTIDA_PEDIDO","APROVADA"].includes(statusCodigo(item))}
function prioridade(item: Proposta) { const valor=statusCodigo(item); if(valor==="CONVERTIDA_PEDIDO")return 60;if(["ACEITA","APROVADA"].includes(valor))return 50;if(["EMITIDA","ENVIADA","VISUALIZADA","EM_NEGOCIACAO"].includes(valor))return 40;if(["APROVADA_INTERNA","EM_REVISAO"].includes(valor))return 30;if(["RASCUNHO","ELABORACAO"].includes(valor))return 20;return 10 }
function correspondeFiltro(item: Proposta, filtro: FiltroProposta) {
  const codigo=statusCodigo(item)
  if(filtro==="TODOS") return true
  if(filtro==="ACEITAS_CONVERTIDAS") return aceitaOuConvertida(item)
  if(filtro==="ELABORACAO") return ["RASCUNHO","ELABORACAO"].includes(codigo)
  if(filtro==="ACEITA") return ["ACEITA","APROVADA"].includes(codigo)
  return codigo===filtro
}

export default function PropostasPage() {
  const { usuario } = useAuth()
  const { locale, tOp, formatCurrency, formatNumber } = useOperationalI18n()
  const tx=textos[locale]
  const [dados,setDados]=useState<Proposta[]>([]),[nucleo,setNucleo]=useState<LinhaNucleo[]>([]),[loading,setLoading]=useState(true),[erro,setErro]=useState(""),[filtro,setFiltro]=useState<FiltroProposta>("TODOS")
  useEffect(()=>{void(async()=>{try{const [rp,rn]=await Promise.all([fetch(`${API_URL}/crm/propostas`,{cache:"no-store"}),fetch(`${API_URL}/crm/nucleo-comercial`,{cache:"no-store"})]);const pp=await rp.json().catch(()=>[]),np=await rn.json().catch(()=>[]);if(!rp.ok)throw new Error(pp?.detail||tx.loading);setDados(Array.isArray(pp)?pp:[]);setNucleo(rn.ok&&Array.isArray(np)?np:[])}catch(e){setErro(e instanceof Error?e.message:tx.loading)}finally{setLoading(false)}})()},[tx.loading])
  const nucleoEscopado=useMemo(()=>nucleo.filter(item=>pertenceAoEscopoDoUsuario(item.responsavel_id,usuario)),[nucleo,usuario])
  const oportunidadesPermitidas=useMemo(()=>new Set(nucleoEscopado.map(item=>String(item.oportunidade_id||"")).filter(Boolean)),[nucleoEscopado])
  const dadosEscopados=useMemo(()=>possuiEscopoProprio(usuario)?dados.filter(item=>Boolean(item.oportunidade_id)&&oportunidadesPermitidas.has(String(item.oportunidade_id))):dados,[dados,oportunidadesPermitidas,usuario])
  const grupos=useMemo<Grupo[]>(()=>{const mapaNucleo=new Map<string,LinhaNucleo>();for(const item of nucleoEscopado){for(const chave of [item.proposta_id,item.proposta_vigente_id,item.oportunidade_id])if(chave)mapaNucleo.set(chave,item)}const mapa=new Map<string,Proposta[]>();for(const proposta of dadosEscopados){const chave=proposta.item_oportunidade_id||proposta.oportunidade_id||proposta.id;mapa.set(chave,[...(mapa.get(chave)||[]),proposta])}return[...mapa.entries()].map(([chave,versoes])=>{const ordenadas=[...versoes].sort((a,b)=>prioridade(b)-prioridade(a)||Number(b.versao||0)-Number(a.versao||0)||String(b.created_at||"").localeCompare(String(a.created_at||"")));const proposta=ordenadas[0],snap=proposta.snapshot_dados,linha=mapaNucleo.get(proposta.id)||mapaNucleo.get(proposta.oportunidade_id||"");return{chave,proposta,versoes:[...versoes].sort((a,b)=>Number(b.versao||0)-Number(a.versao||0)),cliente:linha?.cliente_nome||snap?.oportunidade?.cliente_nome||snap?.oportunidade?.empresa_nome||tx.unidentifiedClient,oportunidade:linha?.titulo||snap?.oportunidade?.titulo||tx.genericOpportunity,validade:proposta.validade||snap?.validade||tx.notProvided}}).sort((a,b)=>String(b.proposta.created_at||"").localeCompare(String(a.proposta.created_at||"")))},[dadosEscopados,nucleoEscopado,tx.genericOpportunity,tx.notProvided,tx.unidentifiedClient])
  const filtrados=grupos.filter(g=>correspondeFiltro(g.proposta,filtro)),valor=grupos.reduce((s,g)=>s+Number(g.proposta.valor||0),0),aceitas=grupos.filter(g=>aceitaOuConvertida(g.proposta)).length
  const statusLabel=(item:Proposta)=>tx.statuses[statusCodigo(item) as keyof typeof tx.statuses] || statusCodigo(item).replaceAll("_"," ")
  const filtroLabel=(valorFiltro:FiltroProposta)=>valorFiltro==="TODOS"?tx.all:valorFiltro==="ACEITAS_CONVERTIDAS"?tx.acceptedConverted:valorFiltro==="ELABORACAO"?tx.statuses.ELABORACAO:valorFiltro==="ACEITA"?tx.statuses.ACEITA:tx.statuses[valorFiltro as keyof typeof tx.statuses] || valorFiltro
  function abrirComposicao(novoFiltro:FiltroProposta){setFiltro(novoFiltro);window.setTimeout(()=>document.getElementById("lista-propostas")?.scrollIntoView({behavior:"smooth",block:"start"}),0)}
  return <main className="flex min-h-screen bg-[#020817]"><Sidebar/><section className="flex-1"><Topbar/><div className="space-y-6 p-8">
    <div><h1 className="text-4xl font-bold text-white">CRM • {tOp("proposals.title")}</h1><p className="mt-2 text-gray-400">{tx.subtitle}</p></div>
    <JornadaComercialNav/>
    {erro&&<div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
    <section className="grid gap-4 md:grid-cols-3"><Kpi titulo={tx.dealsWithProposal} valor={formatNumber(grupos.length)} onOpen={()=>abrirComposicao("TODOS")} detalhe={tx.click}/><Kpi titulo={tx.consolidatedValue} valor={formatCurrency(valor)} onOpen={()=>abrirComposicao("TODOS")} detalhe={tx.click}/><Kpi titulo={tx.acceptedConverted} valor={formatNumber(aceitas)} onOpen={()=>abrirComposicao("ACEITAS_CONVERTIDAS")} detalhe={tx.click}/></section>
    <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-5"><label className="text-sm text-gray-300">{tx.status}<select value={filtro} onChange={e=>setFiltro(e.target.value as FiltroProposta)} className="ml-3 rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white"><option value="TODOS">{tx.all}</option><option value="ACEITAS_CONVERTIDAS">{tx.acceptedConverted}</option><option value="ELABORACAO">{tx.statuses.ELABORACAO}</option><option value="EMITIDA">{tx.statuses.EMITIDA}</option><option value="ENVIADA">{tx.statuses.ENVIADA}</option><option value="EM_NEGOCIACAO">{tx.statuses.EM_NEGOCIACAO}</option><option value="ACEITA">{tx.statuses.ACEITA}</option><option value="CONVERTIDA_PEDIDO">{tx.statuses.CONVERTIDA_PEDIDO}</option><option value="CANCELADA">{tx.statuses.CANCELADA}</option></select></label></section>
    <div id="lista-propostas" className="scroll-mt-24 overflow-hidden rounded-2xl border border-[#13203f] bg-[#091a33]"><div className="border-b border-[#13203f] p-6"><h2 className="text-xl font-semibold text-white">{tx.title}</h2><p className="mt-1 text-sm text-slate-400">{tx.explanation} {tx.currentFilter}: {filtroLabel(filtro)} · {formatNumber(filtrados.length)}.</p></div>{loading?<div className="p-10 text-gray-400">{tx.loading}</div>:<div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b border-[#13203f]"><Th>{tx.client}</Th><Th>{tx.currentProposal}</Th><Th>{tx.opportunity}</Th><Th>{tx.value}</Th><Th>{tx.status}</Th><Th>{tx.validity}</Th><Th>{tx.versions}</Th><Th>{tx.action}</Th></tr></thead><tbody>{filtrados.map(g=><tr key={g.chave} className="border-b border-[#13203f]"><Td>{g.cliente}</Td><Td>{g.proposta.numero||tx.noNumber}</Td><Td>{g.oportunidade}</Td><td className="p-4 text-green-400">{formatCurrency(Number(g.proposta.valor||0))}</td><td className="p-4 text-cyan-400">{statusLabel(g.proposta)}</td><Td>{g.validade}</Td><Td>{formatNumber(g.versoes.length)}</Td><td className="p-4"><div className="flex gap-2"><Link href={`/propostas/${g.proposta.id}`} className="rounded-lg border border-slate-600 px-3 py-2 text-xs text-slate-200">{tx.data}</Link><Link href={`/propostas/${g.proposta.id}/documento`} className="rounded-lg bg-cyan-500 px-3 py-2 text-xs font-semibold text-slate-950">{tx.view}</Link></div></td></tr>)}</tbody></table></div>}</div>
  </div></section></main>
}
function Kpi({titulo,valor,onOpen,detalhe}:{titulo:string;valor:string|number;onOpen?:()=>void;detalhe:string}){const body=<><p className="text-sm text-gray-400">{titulo}</p><h2 className="mt-2 text-3xl font-bold text-cyan-400">{valor}</h2>{onOpen&&<p className="mt-2 text-[11px] text-cyan-400">{detalhe}</p>}</>;return onOpen?<button type="button" onClick={onOpen} className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6 text-left transition hover:border-cyan-500/70 hover:bg-[#0b1d38]">{body}</button>:<div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6">{body}</div>}
function Th({children}:{children:React.ReactNode}){return <th className="p-4 text-left text-gray-400">{children}</th>}
function Td({children}:{children:React.ReactNode}){return <td className="p-4 text-white">{children}</td>}
