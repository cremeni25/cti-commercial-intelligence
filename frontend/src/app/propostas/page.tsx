"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Snapshot = {
  validade?: string | null
  oportunidade?: { titulo?: string; cliente_nome?: string; empresa_nome?: string }
  item?: { nome_comercial?: string; equipamento?: string }
}

type Proposta = {
  id: string
  numero?: string
  cliente_id?: string
  oportunidade_id?: string
  item_oportunidade_id?: string
  valor?: number
  status?: string
  status_documento?: string
  validade?: string
  versao?: number
  created_at?: string
  snapshot_dados?: Snapshot
}

type GrupoProposta = {
  chave: string
  propostaAtual: Proposta
  versoes: Proposta[]
  cliente: string
  oportunidade: string
  validade: string
}

const STATUS_FINAIS = new Set(["ACEITA", "CONVERTIDA_PEDIDO", "REJEITADA", "EXPIRADA", "CANCELADA"])

function normalizarStatus(item: Proposta) {
  const status = String(item.status_documento || item.status || "RASCUNHO").toUpperCase()
  const mapa: Record<string, string> = {
    RASCUNHO: "Em elaboração",
    ELABORACAO: "Em elaboração",
    EM_REVISAO: "Em revisão",
    APROVADA_INTERNA: "Aprovada internamente",
    EMITIDA: "Emitida",
    ENVIADA: "Enviada",
    VISUALIZADA: "Visualizada",
    EM_NEGOCIACAO: "Em negociação",
    APROVADA: "Aceita",
    ACEITA: "Aceita",
    CONVERTIDA_PEDIDO: "Convertida em pedido",
    REJEITADA: "Rejeitada",
    EXPIRADA: "Expirada",
    CANCELADA: "Cancelada",
  }
  return mapa[status] || status.replaceAll("_", " ")
}

function dataValidade(item: Proposta) {
  return item.validade || item.snapshot_dados?.validade || "Não informada"
}

function prioridade(item: Proposta) {
  const status = String(item.status_documento || item.status || "").toUpperCase()
  if (status === "CONVERTIDA_PEDIDO") return 60
  if (status === "ACEITA" || status === "APROVADA") return 50
  if (["EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)) return 40
  if (["APROVADA_INTERNA", "EM_REVISAO"].includes(status)) return 30
  if (["RASCUNHO", "ELABORACAO"].includes(status)) return 20
  return 10
}

export default function PropostasPage() {
  const [dados, setDados] = useState<Proposta[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [statusFiltro, setStatusFiltro] = useState("TODOS")

  useEffect(() => {
    queueMicrotask(async () => {
      try {
        const response = await fetch(`${API_URL}/crm/propostas`, { cache: "no-store" })
        const json = await response.json().catch(() => [])
        if (!response.ok) throw new Error(json?.detail || "Não foi possível carregar as propostas.")
        setDados(Array.isArray(json) ? json : [])
      } catch (falha) {
        setErro(falha instanceof Error ? falha.message : "Não foi possível carregar as propostas operacionais.")
      } finally {
        setLoading(false)
      }
    })
  }, [])

  const grupos = useMemo<GrupoProposta[]>(() => {
    const mapa = new Map<string, Proposta[]>()
    for (const item of dados) {
      const chave = item.item_oportunidade_id || item.oportunidade_id || item.id
      mapa.set(chave, [...(mapa.get(chave) || []), item])
    }

    return Array.from(mapa.entries()).map(([chave, versoes]) => {
      const ordenadas = [...versoes].sort((a, b) => {
        const diferencaStatus = prioridade(b) - prioridade(a)
        if (diferencaStatus !== 0) return diferencaStatus
        const diferencaVersao = Number(b.versao || 0) - Number(a.versao || 0)
        if (diferencaVersao !== 0) return diferencaVersao
        return String(b.created_at || "").localeCompare(String(a.created_at || ""))
      })
      const propostaAtual = ordenadas[0]
      const snapshot = propostaAtual.snapshot_dados
      return {
        chave,
        propostaAtual,
        versoes: [...versoes].sort((a, b) => Number(b.versao || 0) - Number(a.versao || 0)),
        cliente: snapshot?.oportunidade?.cliente_nome || snapshot?.oportunidade?.empresa_nome || propostaAtual.cliente_id || "Cliente não identificado",
        oportunidade: snapshot?.oportunidade?.titulo || propostaAtual.oportunidade_id || "Oportunidade não identificada",
        validade: dataValidade(propostaAtual),
      }
    }).sort((a, b) => String(b.propostaAtual.created_at || "").localeCompare(String(a.propostaAtual.created_at || "")))
  }, [dados])

  const gruposFiltrados = useMemo(() => grupos.filter((grupo) => {
    if (statusFiltro === "TODOS") return true
    return normalizarStatus(grupo.propostaAtual) === statusFiltro
  }), [grupos, statusFiltro])

  const valorTotal = grupos.reduce((acc, grupo) => acc + Number(grupo.propostaAtual.valor || 0), 0)
  const aprovadas = grupos.filter((grupo) => ["ACEITA", "CONVERTIDA_PEDIDO", "APROVADA"].includes(String(grupo.propostaAtual.status_documento || grupo.propostaAtual.status || "").toUpperCase())).length
  const emAndamento = grupos.filter((grupo) => !STATUS_FINAIS.has(String(grupo.propostaAtual.status_documento || grupo.propostaAtual.status || "").toUpperCase())).length

  return <main className="flex min-h-screen bg-[#020817]"><Sidebar /><section className="flex-1"><Topbar /><div className="space-y-6 p-8">
    <div><h1 className="text-4xl font-bold text-white">CRM • Propostas</h1><p className="mt-2 text-gray-400">Visão consolidada das negociações. Versões não são somadas como propostas independentes.</p></div>
    {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

    <section className="grid grid-cols-1 gap-4 md:grid-cols-3"><Kpi titulo="Negociações com proposta" valor={grupos.length} /><Kpi titulo="Valor comercial consolidado" valor={`R$ ${valorTotal.toLocaleString("pt-BR")}`} /><Kpi titulo="Em andamento" valor={emAndamento} /><Kpi titulo="Aceitas / convertidas" valor={aprovadas} /></section>

    <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between"><div><h2 className="font-semibold text-white">Filtro próprio de Propostas</h2><p className="mt-1 text-sm text-gray-400">Este filtro atua apenas nesta tela.</p></div><label className="text-sm text-gray-300">Status<select value={statusFiltro} onChange={(evento) => setStatusFiltro(evento.target.value)} className="ml-3 rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white"><option value="TODOS">Todos</option><option value="Em elaboração">Em elaboração</option><option value="Emitida">Emitida</option><option value="Enviada">Enviada</option><option value="Em negociação">Em negociação</option><option value="Aceita">Aceita</option><option value="Convertida em pedido">Convertida em pedido</option><option value="Cancelada">Cancelada</option></select></label></div>
    </section>

    <div className="overflow-hidden rounded-2xl border border-[#13203f] bg-[#091a33]"><div className="border-b border-[#13203f] p-6"><h2 className="text-xl font-semibold text-white">Propostas Comerciais</h2></div>{loading ? <div className="p-10 text-gray-400">Carregando...</div> : gruposFiltrados.length === 0 ? <div className="p-10 text-gray-400">Nenhuma negociação encontrada para o filtro selecionado.</div> : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b border-[#13203f]"><th className="p-4 text-left text-gray-400">Cliente</th><th className="p-4 text-left text-gray-400">Proposta vigente</th><th className="p-4 text-left text-gray-400">Oportunidade</th><th className="p-4 text-left text-gray-400">Valor</th><th className="p-4 text-left text-gray-400">Status</th><th className="p-4 text-left text-gray-400">Validade</th><th className="p-4 text-left text-gray-400">Versões</th></tr></thead><tbody>{gruposFiltrados.map((grupo) => <tr key={grupo.chave} className="border-b border-[#13203f]"><td className="p-4 text-white">{grupo.cliente}</td><td className="p-4 text-white">{grupo.propostaAtual.numero || grupo.propostaAtual.id}</td><td className="p-4 text-gray-300">{grupo.oportunidade}</td><td className="p-4 text-green-400">R$ {Number(grupo.propostaAtual.valor || 0).toLocaleString("pt-BR")}</td><td className="p-4 text-cyan-400">{normalizarStatus(grupo.propostaAtual)}</td><td className="p-4 text-white">{grupo.validade}</td><td className="p-4 text-gray-300">{grupo.versoes.length}</td></tr>)}</tbody></table></div>}</div>
  </div></section></main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><h2 className="mt-2 text-3xl font-bold text-cyan-400">{valor}</h2></div> }
