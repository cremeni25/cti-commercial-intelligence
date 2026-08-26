/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import JornadaComercialNav from "@/components/crm/JornadaComercialNav"
import { API_URL } from "@/lib/api"
import { lerContextoOportunidade } from "@/lib/crm-opportunity"

type Oportunidade = {
  id: string
  titulo: string
  cliente_nome: string
  status: string
  descricao?: string
  valor_estimado: number
  probabilidade: number
  data_fechamento_prevista?: string | null
  equipamento?: string
  linha_equipamentos?: string
  created_at?: string
}
type ItemOportunidade = { nome_comercial?: string; equipamento?: string; modelo_base?: string; linha_produto?: string; quantidade?: number; arquivado_em?: string | null }

type VisaoOportunidade = "TODAS" | "ABERTAS"

function moeda(valor: number) { return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function percentual(valor?: number) { const numero = Number(valor || 0); return Math.round(numero <= 1 ? numero * 100 : numero) }
function chanceDaOportunidade(item: Oportunidade) {
  const status = String(item.status || "").toUpperCase()
  if (["GANHO", "PEDIDO", "DOSSIÊ", "CARRIER", "FATURADO", "ENCERRADO"].includes(status)) return 100
  if (["PERDIDO", "CANCELADO"].includes(status)) return 0
  return percentual(item.probabilidade)
}
function oportunidadeAberta(item: Oportunidade) { return !["GANHO", "PERDIDO", "CANCELADO"].includes(String(item.status || "").toUpperCase()) }
function dataIsoValida(valor?: string | null) { return Boolean(valor && /^\d{4}-\d{2}-\d{2}$/.test(valor.slice(0, 10)) && !Number.isNaN(new Date(`${valor.slice(0, 10)}T12:00:00`).getTime())) }
function dataPrevista(valor?: string | null) { return dataIsoValida(valor) ? new Date(`${String(valor).slice(0, 10)}T12:00:00`).toLocaleDateString("pt-BR") : "Sem previsão" }
function inicioMesAtual() { const agora = new Date(); return `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, "0")}-01` }
function fimMesAtual() { const agora = new Date(); return new Date(agora.getFullYear(), agora.getMonth() + 1, 0).toISOString().slice(0, 10) }
function unicos(valores: string[]) { const vistos = new Set<string>(); return valores.filter((valor) => { const chave = valor.trim().toUpperCase(); if (!chave || vistos.has(chave)) return false; vistos.add(chave); return true }) }
async function enriquecerComItens(item: Oportunidade): Promise<Oportunidade> {
  try {
    const resposta = await fetch(`/api/crm-proxy/crm-documentos/oportunidades/${encodeURIComponent(item.id)}/itens`, { cache: "no-store" })
    const payload = await resposta.json().catch(() => [])
    if (!resposta.ok || !Array.isArray(payload)) return item
    const ativos = (payload as ItemOportunidade[]).filter((registro) => !registro.arquivado_em)
    const equipamentos = unicos(ativos.map((registro) => String(registro.nome_comercial || registro.equipamento || registro.modelo_base || "").trim()).filter(Boolean))
    const linhas = unicos(ativos.map((registro) => String(registro.linha_produto || "").trim()).filter(Boolean))
    return { ...item, equipamento: equipamentos.join(", ") || item.equipamento, linha_equipamentos: linhas.join(", ") || item.linha_equipamentos }
  } catch {
    return item
  }
}

export default function OportunidadesPage() {
  const [dados, setDados] = useState<Oportunidade[]>([])
  const [inicio, setInicio] = useState(inicioMesAtual)
  const [fim, setFim] = useState(fimMesAtual)
  const [busca, setBusca] = useState("")
  const [visao, setVisao] = useState<VisaoOportunidade>("TODAS")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")
    fetch(`${API_URL}/crm-visao/oportunidades?inicio=${inicio}&fim=${fim}`, { cache: "no-store" })
      .then(async (response) => { if (!response.ok) throw new Error("Falha ao carregar oportunidades"); return response.json() as Promise<Oportunidade[]> })
      .then(async (registros) => {
        const base = Array.isArray(registros) ? registros : []
        const enriquecidos = await Promise.all(base.map(enriquecerComItens))
        if (ativo) setDados(enriquecidos)
      })
      .catch(() => { if (ativo) setErro("Não foi possível carregar as oportunidades do período.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [inicio, fim])

  const abertas = useMemo(() => dados.filter(oportunidadeAberta), [dados])
  const filtrados = useMemo(() => {
    const base = visao === "ABERTAS" ? abertas : dados
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return base
    return base.filter((item) => `${item.cliente_nome} ${item.titulo} ${item.status} ${item.equipamento || ""} ${item.linha_equipamentos || ""}`.toLocaleLowerCase("pt-BR").includes(termo))
  }, [abertas, busca, dados, visao])

  const valorTotal = abertas.reduce((total, item) => total + Number(item.valor_estimado || 0), 0)
  const valorPonderado = abertas.reduce((total, item) => total + Number(item.valor_estimado || 0) * (chanceDaOportunidade(item) / 100), 0)
  const relatorioHref = `/oportunidades/relatorio?inicio=${encodeURIComponent(inicio)}&fim=${encodeURIComponent(fim)}&busca=${encodeURIComponent(busca)}`

  function abrirComposicao(novaVisao: VisaoOportunidade) {
    setVisao(novaVisao)
    setBusca("")
    window.setTimeout(() => document.getElementById("lista-oportunidades")?.scrollIntoView({ behavior: "smooth", block: "start" }), 0)
  }

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Negócio individual</p><h1 className="mt-2 text-3xl font-bold sm:text-4xl">CRM • Oportunidades</h1><p className="mt-2 text-gray-400">Fonte operacional do negócio: cliente, composição de itens, valor, chance, próxima ação e previsão de fechamento.</p></div><div className="flex flex-col gap-3 sm:flex-row"><Link href={relatorioHref} className="rounded-xl border border-cyan-700 px-5 py-3 text-center font-semibold text-cyan-300">Gerar relatório</Link><Link href="/crm-app/oportunidades/nova" className="rounded-xl bg-cyan-500 px-5 py-3 text-center font-semibold text-slate-950">Nova oportunidade</Link></div></header>
    <JornadaComercialNav />
    <section className="grid gap-4 rounded-2xl border border-[#13203f] bg-[#071226] p-5 md:grid-cols-2 xl:grid-cols-[1fr_1fr_2fr_auto]"><CampoData label="Início" value={inicio} onChange={setInicio} /><CampoData label="Fim" value={fim} onChange={setFim} /><label className="text-sm text-slate-300">Buscar<input value={busca} onChange={(event) => setBusca(event.target.value)} placeholder="Empresa, oportunidade, produto ou etapa" className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" /></label><button type="button" onClick={() => { setInicio(inicioMesAtual()); setFim(fimMesAtual()) }} className="self-end rounded-xl border border-cyan-700 px-4 py-3 text-cyan-300">Mês atual</button></section>
    {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Kpi titulo="Registros no período" valor={dados.length.toLocaleString("pt-BR")} onOpen={() => abrirComposicao("TODAS")} /><Kpi titulo="Oportunidades abertas" valor={abertas.length.toLocaleString("pt-BR")} onOpen={() => abrirComposicao("ABERTAS")} /><Kpi titulo="Valor aberto" valor={moeda(valorTotal)} onOpen={() => abrirComposicao("ABERTAS")} /><Kpi titulo="Valor ponderado" valor={moeda(valorPonderado)} onOpen={() => abrirComposicao("ABERTAS")} /></section>
    <section className="flex flex-wrap gap-2"><button type="button" onClick={() => setVisao("TODAS")} className={`rounded-full border px-4 py-2 text-sm ${visao === "TODAS" ? "border-cyan-500 bg-cyan-950/50 text-cyan-200" : "border-[#24466f] bg-[#020817] text-slate-400"}`}>Todas <strong className="ml-1">{dados.length}</strong></button><button type="button" onClick={() => setVisao("ABERTAS")} className={`rounded-full border px-4 py-2 text-sm ${visao === "ABERTAS" ? "border-cyan-500 bg-cyan-950/50 text-cyan-200" : "border-[#24466f] bg-[#020817] text-slate-400"}`}>Abertas <strong className="ml-1">{abertas.length}</strong></button></section>
    <div id="lista-oportunidades" className="scroll-mt-24 overflow-x-auto rounded-2xl border border-[#13203f] bg-[#091a33]">{loading ? <Aviso>Carregando oportunidades...</Aviso> : filtrados.length === 0 ? <Aviso>Nenhuma oportunidade encontrada no período.</Aviso> : <><div className="border-b border-[#13203f] px-5 py-3 text-xs text-cyan-300">Composição atual: {filtrados.length.toLocaleString("pt-BR")} oportunidade(s) · visão {visao === "ABERTAS" ? "Abertas" : "Todas"}.</div><table className="min-w-[1050px] w-full text-left text-sm"><thead className="bg-[#061326] text-xs uppercase text-slate-500"><tr><th className="px-5 py-4">Empresa</th><th className="px-5 py-4">Oportunidade</th><th className="px-5 py-4">Produtos da oportunidade</th><th className="px-5 py-4">Valor</th><th className="px-5 py-4">Chance</th><th className="px-5 py-4">Etapa</th><th className="px-5 py-4">Previsão</th><th className="px-5 py-4">Ação</th></tr></thead><tbody className="divide-y divide-[#13203f]">{filtrados.map((item) => { const contexto = lerContextoOportunidade(item); return <tr key={item.id} className="align-middle text-slate-200"><td className="px-5 py-4 font-semibold text-cyan-300">{item.cliente_nome}</td><td className="px-5 py-4 font-medium">{item.titulo}</td><td className="px-5 py-4">{item.equipamento || contexto.equipamentos.join(", ") || item.linha_equipamentos || "A definir"}</td><td className="px-5 py-4 text-emerald-300">{moeda(Number(item.valor_estimado || 0))}</td><td className="px-5 py-4">{chanceDaOportunidade(item)}%</td><td className="px-5 py-4">{item.status}</td><td className="px-5 py-4">{dataPrevista(item.data_fechamento_prevista)}</td><td className="px-5 py-4"><Link href={`/oportunidades/${item.id}`} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300">Abrir negócio</Link></td></tr> })}</tbody></table></>}</div>
  </div></section></main>
}

function CampoData({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label className="text-sm text-slate-300">{label}<input type="date" value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" /></label> }
function Kpi({ titulo, valor, onOpen }: { titulo: string; valor: string; onOpen?: () => void }) { const body = <><p className="text-sm text-gray-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-400">{valor}</p>{onOpen && <p className="mt-2 text-[11px] text-cyan-400">Clique para detalhar</p>}</>; return onOpen ? <button type="button" onClick={onOpen} className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5 text-left transition hover:border-cyan-500/70 hover:bg-[#0b1d38]">{body}</button> : <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5">{body}</div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="p-10 text-gray-300">{children}</div> }
