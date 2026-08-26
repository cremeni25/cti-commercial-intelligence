"use client"

import { Suspense, useMemo, useState } from "react"
import { ArrowLeft, FileText, Printer, Search } from "lucide-react"
import { useRouter, useSearchParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getDrilldown, type DrilldownResultado } from "@/services/modulos-api"

type Camada = "anfir" | "historico" | "crm"
type CampoOpcao = { valor: string; rotulo: string }

const CAMPOS: Record<Camada, CampoOpcao[]> = {
  anfir: [
    { valor: "", rotulo: "Todos os registros" },
    { valor: "estado", rotulo: "UF / Estado" },
    { valor: "municipio", rotulo: "Município" },
    { valor: "ddd", rotulo: "DDD" },
    { valor: "implementadora", rotulo: "Implementadora" },
    { valor: "empresa", rotulo: "Empresa / Cliente" },
    { valor: "equipamento", rotulo: "Equipamento / Linha" },
    { valor: "familia", rotulo: "Família TR / DT / DD" },
  ],
  historico: [
    { valor: "", rotulo: "Todos os registros" },
    { valor: "aba", rotulo: "Origem / Aba" },
    { valor: "ano", rotulo: "Ano" },
    { valor: "canal", rotulo: "Canal de venda" },
    { valor: "representante", rotulo: "Responsável comercial" },
    { valor: "status", rotulo: "Status" },
    { valor: "equipamento", rotulo: "Equipamento" },
    { valor: "implementadora", rotulo: "Implementadora" },
    { valor: "motivo_perda", rotulo: "Motivo de perda" },
    { valor: "empresa", rotulo: "Empresa / Cliente" },
    { valor: "familia", rotulo: "Família TR / DT / DD" },
  ],
  crm: [
    { valor: "", rotulo: "Todas as oportunidades em curso" },
    { valor: "estado", rotulo: "UF / Estado" },
    { valor: "municipio", rotulo: "Município" },
    { valor: "ddd", rotulo: "DDD" },
    { valor: "equipamento", rotulo: "Equipamento" },
    { valor: "status", rotulo: "Status" },
    { valor: "empresa", rotulo: "Empresa / Cliente" },
    { valor: "familia", rotulo: "Família TR / DT / DD" },
  ],
}

const ROTULOS: Record<string, string> = {
  aba_origem: "Aba", linha_origem: "Linha", data: "Data", ano: "Ano", cliente: "Cliente",
  cliente_nome: "Cliente", empresa: "Empresa", transportadora: "Transportadora", equipamento: "Equipamento",
  modelo: "Modelo", linha: "Linha / família", linha_equipamentos: "Linha / família", produto: "Produto",
  quantidade: "Quantidade", valor_unitario: "Valor unitário", valor_total: "Valor total", valor_estimado: "Valor estimado",
  valor: "Valor", representante_original: "Responsável original", representante_atual: "Responsável atual", status: "Status",
  motivo_perda: "Motivo de perda", canal_venda: "Canal", implementadora: "Implementadora", estado: "UF", cidade: "Cidade",
  municipio: "Município", ddd: "DDD", previsao: "Previsão", probabilidade: "Probabilidade", observacao: "Observação",
  titulo: "Título", data_fechamento_prevista: "Fechamento previsto", created_at: "Criado em", id: "ID",
}

function ModularPageContent() {
  const router = useRouter()
  const params = useSearchParams()
  const [camada, setCamada] = useState<Camada>((params.get("camada") as Camada) || "anfir")
  const [campo, setCampo] = useState(params.get("campo") || "")
  const [valor, setValor] = useState(params.get("valor") || "")
  const [familia, setFamilia] = useState(params.get("familia") || "")
  const [contexto, setContexto] = useState(params.get("contexto") || "viena-sp")
  const [periodo, setPeriodo] = useState(params.get("periodo") || "TODO_HISTORICO")
  const [inicio, setInicio] = useState(params.get("inicio") || "")
  const [fim, setFim] = useState(params.get("fim") || "")
  const [uf, setUf] = useState(params.get("uf") || "")
  const [ddd, setDdd] = useState(params.get("ddd") || "")
  const [busca, setBusca] = useState(params.get("busca") || "")
  const [titulo, setTitulo] = useState(params.get("titulo") || "Relatório CTI")
  const [dados, setDados] = useState<DrilldownResultado | null>(null)
  const [registros, setRegistros] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState("")

  const colunas = useMemo(() => {
    const conjunto = new Set<string>()
    registros.forEach((registro) => Object.keys(registro).forEach((chave) => conjunto.add(chave)))
    return Array.from(conjunto)
  }, [registros])

  async function gerar() {
    setLoading(true)
    setErro("")
    setDados(null)
    setRegistros([])
    try {
      const base = new URLSearchParams({ camada, contexto, periodo, pagina: "1", limite: "100" })
      if (campo) base.set("campo", campo)
      if (valor.trim()) base.set("valor", valor.trim())
      if (familia) base.set("familia", familia)
      if (inicio) base.set("inicio", inicio)
      if (fim) base.set("fim", fim)
      if (uf) base.set("uf", uf)
      if (ddd) base.set("ddd", ddd)
      if (busca.trim()) base.set("busca", busca.trim())

      const primeira = await getDrilldown(base.toString())
      const todos = [...primeira.registros]
      for (let pagina = 2; pagina <= primeira.total_paginas; pagina += 1) {
        const proxima = new URLSearchParams(base)
        proxima.set("pagina", String(pagina))
        const lote = await getDrilldown(proxima.toString())
        todos.push(...lote.registros)
      }
      setDados(primeira)
      setRegistros(todos)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível gerar o relatório.")
    } finally {
      setLoading(false)
    }
  }

  const camadaRotulo = camada === "anfir" ? "ANFIR" : camada === "historico" ? "Histórico Comercial" : "CRM em curso"
  const filtroRotulo = campo ? `${CAMPOS[camada].find((item) => item.valor === campo)?.rotulo || campo}: ${valor || "todos"}` : "Todos os registros"

  return <main className="flex min-h-screen bg-[#020817] text-white print:block print:bg-white print:text-black">
    <div className="print:hidden"><Sidebar /></div>
    <section className="min-w-0 flex-1">
      <div className="print:hidden"><Topbar /></div>
      <div className="space-y-5 p-4 sm:p-6 lg:p-8 print:p-0">
        <header className="rounded-3xl border border-[#17304d] bg-[#071226] p-6 print:rounded-none print:border-0 print:bg-white print:p-0">
          <button onClick={() => router.push("/relatorios")} className="mb-4 inline-flex items-center gap-2 rounded-xl border border-[#17304d] px-4 py-2 text-sm text-cyan-200 print:hidden"><ArrowLeft size={16}/> Voltar aos Relatórios</button>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div><p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400 print:text-black">Gerador modular</p><h1 className="mt-2 text-3xl font-bold">{titulo}</h1><p className="mt-2 text-sm text-slate-400 print:text-gray-700">{camadaRotulo} · {filtroRotulo}</p></div>
            {dados && <div className="rounded-2xl border border-cyan-500/30 px-5 py-4 text-right print:border-gray-400"><p className="text-xs uppercase text-slate-500">Total</p><strong className="text-3xl text-cyan-300 print:text-black">{dados.total_registros.toLocaleString("pt-BR")}</strong></div>}
          </div>
        </header>

        <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5 print:hidden">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <label className="text-sm text-slate-300">Título do relatório<input value={titulo} onChange={(e) => setTitulo(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label>
            <label className="text-sm text-slate-300">Módulo / camada<select value={camada} onChange={(e) => { setCamada(e.target.value as Camada); setCampo(""); setValor("") }} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"><option value="anfir">ANFIR</option><option value="historico">Histórico Comercial</option><option value="crm">CRM em curso</option></select></label>
            <label className="text-sm text-slate-300">Recorte<select value={campo} onChange={(e) => { setCampo(e.target.value); setValor("") }} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3">{CAMPOS[camada].map((item) => <option key={item.valor} value={item.valor}>{item.rotulo}</option>)}</select></label>
            <label className="text-sm text-slate-300">Valor do recorte<input value={valor} onChange={(e) => setValor(e.target.value)} disabled={!campo} placeholder={campo ? "Ex.: 11, SP, PERDIDO..." : "Não necessário"} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 disabled:opacity-50"/></label>
            <label className="text-sm text-slate-300">Família<select value={familia} onChange={(e) => setFamilia(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"><option value="">Todas</option><option value="TR">TR · Trailer</option><option value="DT">DT · Diesel Truck</option><option value="DD">DD · Direct Drive</option></select></label>
            <label className="text-sm text-slate-300">Contexto<select value={contexto} onChange={(e) => setContexto(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"><option value="viena-sp">Viena SP</option><option value="brasil">Brasil</option></select></label>
            <label className="text-sm text-slate-300">Período<select value={periodo} onChange={(e) => setPeriodo(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"><option value="TODO_HISTORICO">Todo histórico</option><option value="PERSONALIZADO">Personalizado</option><option value="ANO_ATUAL">Ano atual</option></select></label>
            <label className="text-sm text-slate-300">Busca livre<input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Cliente, equipamento, observação..." className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label>
            <label className="text-sm text-slate-300">Data inicial<input type="date" value={inicio} onChange={(e) => setInicio(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label>
            <label className="text-sm text-slate-300">Data final<input type="date" value={fim} onChange={(e) => setFim(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label>
            <label className="text-sm text-slate-300">UF<input value={uf} onChange={(e) => setUf(e.target.value.toUpperCase())} maxLength={2} placeholder="SP" className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label>
            <label className="text-sm text-slate-300">DDD<input value={ddd} onChange={(e) => setDdd(e.target.value)} placeholder="11" className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label>
          </div>
          <div className="mt-5 flex flex-wrap gap-3"><button onClick={gerar} disabled={loading} className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"><Search size={17}/>{loading ? "Gerando..." : "Gerar relatório"}</button>{dados && <button onClick={() => window.print()} className="inline-flex items-center gap-2 rounded-xl border border-cyan-600 px-5 py-3 font-semibold text-cyan-200"><Printer size={17}/> Imprimir / Salvar PDF</button>}</div>
        </section>

        {erro && <div className="rounded-xl border border-red-500/50 bg-red-950/20 p-4 text-red-200 print:hidden">{erro}</div>}
        {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400 print:hidden">Carregando todos os registros do recorte...</div>}

        {dados && !loading && <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5 print:border-0 print:bg-white print:p-0">
          <div className="mb-4 flex items-center gap-2 text-sm text-slate-400 print:text-gray-700"><FileText size={17}/><span>Fonte: {camadaRotulo} · {dados.total_registros.toLocaleString("pt-BR")} registros · emissão {new Date().toLocaleString("pt-BR")}</span></div>
          {registros.length === 0 ? <div className="p-8 text-center text-slate-500">Nenhum registro encontrado.</div> : <div className="overflow-x-auto print:overflow-visible"><table className="min-w-full border-collapse text-xs"><thead><tr className="border-b border-[#24466f] print:border-gray-400">{colunas.map((chave) => <th key={chave} className="px-3 py-2 text-left uppercase text-slate-500 print:text-black">{ROTULOS[chave] || chave.replaceAll("_", " ")}</th>)}</tr></thead><tbody>{registros.map((registro, indice) => <tr key={indice} className="border-b border-[#13203f] print:border-gray-200">{colunas.map((chave) => <td key={chave} className="max-w-[320px] px-3 py-2 align-top text-slate-300 print:text-black">{formatar(registro[chave], chave)}</td>)}</tr>)}</tbody></table></div>}
        </section>}
      </div>
    </section>
  </main>
}

export default function ModularPage() {
  return <Suspense fallback={<div className="min-h-screen bg-[#020817] p-8 text-slate-400">Carregando gerador de relatórios...</div>}><ModularPageContent/></Suspense>
}

function formatar(valor: unknown, chave: string) {
  if (valor === null || valor === undefined || valor === "") return "—"
  if (Array.isArray(valor)) return valor.join(", ") || "—"
  if (typeof valor === "object") return JSON.stringify(valor)
  if (typeof valor === "number" && (chave.includes("valor") || chave.includes("preco"))) return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
  if (typeof valor === "number") return valor.toLocaleString("pt-BR")
  return String(valor)
}
