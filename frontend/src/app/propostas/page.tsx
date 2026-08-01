"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Snapshot = { validade?: string | null; oportunidade?: { titulo?: string; cliente_nome?: string; empresa_nome?: string } }
type Proposta = { id: string; numero?: string; cliente_id?: string; oportunidade_id?: string; item_oportunidade_id?: string; valor?: number; status?: string; status_documento?: string; validade?: string; versao?: number; created_at?: string; snapshot_dados?: Snapshot }
type Grupo = { chave: string; proposta: Proposta; versoes: Proposta[]; cliente: string; oportunidade: string; validade: string }

function status(item: Proposta) {
  const valor = String(item.status_documento || item.status || "RASCUNHO").toUpperCase()
  const mapa: Record<string, string> = { RASCUNHO:"Em elaboração", ELABORACAO:"Em elaboração", EM_REVISAO:"Em revisão", APROVADA_INTERNA:"Aprovada internamente", EMITIDA:"Emitida", ENVIADA:"Enviada", VISUALIZADA:"Visualizada", EM_NEGOCIACAO:"Em negociação", APROVADA:"Aceita", ACEITA:"Aceita", CONVERTIDA_PEDIDO:"Convertida em pedido", SUBSTITUIDA:"Substituída", REJEITADA:"Rejeitada", EXPIRADA:"Expirada", CANCELADA:"Cancelada" }
  return mapa[valor] || valor.replaceAll("_", " ")
}

function prioridade(item: Proposta) {
  const valor = String(item.status_documento || item.status || "").toUpperCase()
  if (valor === "CONVERTIDA_PEDIDO") return 60
  if (["ACEITA","APROVADA"].includes(valor)) return 50
  if (["EMITIDA","ENVIADA","VISUALIZADA","EM_NEGOCIACAO"].includes(valor)) return 40
  if (["APROVADA_INTERNA","EM_REVISAO"].includes(valor)) return 30
  if (["RASCUNHO","ELABORACAO"].includes(valor)) return 20
  return 10
}

export default function PropostasPage() {
  const [dados, setDados] = useState<Proposta[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [filtro, setFiltro] = useState("TODOS")

  useEffect(() => { void (async () => { try { const r = await fetch(`${API_URL}/crm/propostas`, { cache:"no-store" }); const j = await r.json().catch(()=>[]); if (!r.ok) throw new Error(j?.detail || "Não foi possível carregar as propostas."); setDados(Array.isArray(j)?j:[]) } catch (e) { setErro(e instanceof Error ? e.message : "Falha ao carregar propostas.") } finally { setLoading(false) } })() }, [])

  const grupos = useMemo<Grupo[]>(() => {
    const mapa = new Map<string, Proposta[]>()
    for (const proposta of dados) { const chave = proposta.item_oportunidade_id || proposta.oportunidade_id || proposta.id; mapa.set(chave, [...(mapa.get(chave)||[]), proposta]) }
    return [...mapa.entries()].map(([chave, versoes]) => {
      const ordenadas = [...versoes].sort((a,b)=> prioridade(b)-prioridade(a) || Number(b.versao||0)-Number(a.versao||0) || String(b.created_at||"").localeCompare(String(a.created_at||"")))
      const proposta = ordenadas[0]
      const snap = proposta.snapshot_dados
      return { chave, proposta, versoes:[...versoes].sort((a,b)=>Number(b.versao||0)-Number(a.versao||0)), cliente:snap?.oportunidade?.cliente_nome || snap?.oportunidade?.empresa_nome || proposta.cliente_id || "Cliente não identificado", oportunidade:snap?.oportunidade?.titulo || proposta.oportunidade_id || "Oportunidade não identificada", validade:proposta.validade || snap?.validade || "Não informada" }
    }).sort((a,b)=>String(b.proposta.created_at||"").localeCompare(String(a.proposta.created_at||"")))
  }, [dados])

  const filtrados = grupos.filter((g)=>filtro === "TODOS" || status(g.proposta) === filtro)
  const valor = grupos.reduce((s,g)=>s+Number(g.proposta.valor||0),0)
  const aceitas = grupos.filter((g)=>["ACEITA","CONVERTIDA_PEDIDO","APROVADA"].includes(String(g.proposta.status_documento || g.proposta.status || "").toUpperCase())).length

  return <main className="flex min-h-screen bg-[#020817]"><Sidebar/><section className="flex-1"><Topbar/><div className="space-y-6 p-8">
    <div><h1 className="text-4xl font-bold text-white">CRM • Propostas</h1><p className="mt-2 text-gray-400">Negociações consolidadas e documentos oficiais Carrier.</p></div>
    {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
    <section className="grid gap-4 md:grid-cols-3"><Kpi titulo="Negociações com proposta" valor={grupos.length}/><Kpi titulo="Valor comercial consolidado" valor={`R$ ${valor.toLocaleString("pt-BR")}`}/><Kpi titulo="Aceitas / convertidas" valor={aceitas}/></section>
    <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-5"><label className="text-sm text-gray-300">Status<select value={filtro} onChange={(e)=>setFiltro(e.target.value)} className="ml-3 rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white"><option value="TODOS">Todos</option><option>Em elaboração</option><option>Emitida</option><option>Enviada</option><option>Em negociação</option><option>Aceita</option><option>Convertida em pedido</option><option>Cancelada</option></select></label></section>
    <div className="overflow-hidden rounded-2xl border border-[#13203f] bg-[#091a33]"><div className="border-b border-[#13203f] p-6"><h2 className="text-xl font-semibold text-white">Propostas Comerciais</h2></div>{loading ? <div className="p-10 text-gray-400">Carregando...</div> : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b border-[#13203f]"><Th>Cliente</Th><Th>Proposta vigente</Th><Th>Oportunidade</Th><Th>Valor</Th><Th>Status</Th><Th>Validade</Th><Th>Versões</Th><Th>Ação</Th></tr></thead><tbody>{filtrados.map((g)=><tr key={g.chave} className="border-b border-[#13203f]"><Td>{g.cliente}</Td><Td>{g.proposta.numero || g.proposta.id}</Td><Td>{g.oportunidade}</Td><td className="p-4 text-green-400">R$ {Number(g.proposta.valor||0).toLocaleString("pt-BR")}</td><td className="p-4 text-cyan-400">{status(g.proposta)}</td><Td>{g.validade}</Td><Td>{String(g.versoes.length)}</Td><td className="p-4"><div className="flex gap-2"><Link href={`/propostas/${g.proposta.id}`} className="rounded-lg border border-slate-600 px-3 py-2 text-xs text-slate-200">Dados</Link><Link href={`/propostas/${g.proposta.id}/documento`} className="rounded-lg bg-cyan-500 px-3 py-2 text-xs font-semibold text-slate-950">Visualizar proposta</Link></div></td></tr>)}</tbody></table></div>}</div>
  </div></section></main>
}

function Kpi({titulo,valor}:{titulo:string;valor:string|number}){return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><h2 className="mt-2 text-3xl font-bold text-cyan-400">{valor}</h2></div>}
function Th({children}:{children:React.ReactNode}){return <th className="p-4 text-left text-gray-400">{children}</th>}
function Td({children}:{children:React.ReactNode}){return <td className="p-4 text-white">{children}</td>}
