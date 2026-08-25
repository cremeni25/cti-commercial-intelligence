"use client"

import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, ChevronLeft, ChevronRight, Search } from "lucide-react"
import { useRouter, useSearchParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getDrilldown, type DrilldownResultado } from "@/services/modulos-api"

const ROTULOS: Record<string, string> = {
  aba_origem: "Aba",
  linha_origem: "Linha",
  data: "Data",
  ano: "Ano",
  cliente: "Cliente",
  cliente_nome: "Cliente",
  empresa: "Empresa",
  transportadora: "Transportadora",
  equipamento: "Equipamento",
  modelo: "Modelo",
  linha: "Linha / família",
  linha_equipamentos: "Linha / família",
  produto: "Produto",
  quantidade: "Quantidade",
  valor_unitario: "Valor unitário",
  valor_total: "Valor total",
  valor_estimado: "Valor estimado",
  valor: "Valor",
  representante_original: "Responsável original",
  representante_atual: "Responsável atual",
  status: "Status",
  motivo_perda: "Motivo de perda",
  canal_venda: "Canal",
  implementadora: "Implementadora",
  estado: "UF",
  cidade: "Cidade",
  municipio: "Município",
  ddd: "DDD",
  previsao: "Previsão",
  probabilidade: "Probabilidade",
  observacao: "Observação",
  titulo: "Título",
  data_fechamento_prevista: "Fechamento previsto",
  created_at: "Criado em",
}

export default function DetalhamentoPage() {
  const router = useRouter()
  const params = useSearchParams()
  const [dados, setDados] = useState<DrilldownResultado | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState(params.get("busca") || "")
  const [buscaAplicada, setBuscaAplicada] = useState(params.get("busca") || "")
  const [pagina, setPagina] = useState(Math.max(1, Number(params.get("pagina") || 1)))

  const titulo = params.get("titulo") || "Detalhamento do indicador"
  const subtitulo = params.get("subtitulo") || "Registros que formam o total selecionado"

  const queryBase = useMemo(() => {
    const permitido = ["camada", "campo", "valor", "familia", "contexto", "periodo", "uf", "ddd", "inicio", "fim", "ordenar", "direcao"]
    const destino = new URLSearchParams()
    permitido.forEach((chave) => {
      const valor = params.get(chave)
      if (valor) destino.set(chave, valor)
    })
    return destino
  }, [params])

  useEffect(() => {
    let ativo = true
    const query = new URLSearchParams(queryBase)
    query.set("pagina", String(pagina))
    query.set("limite", "50")
    if (buscaAplicada.trim()) query.set("busca", buscaAplicada.trim())
    setLoading(true)
    setErro("")
    getDrilldown(query.toString())
      .then((resultado) => { if (ativo) setDados(resultado) })
      .catch((error) => { if (ativo) setErro(error instanceof Error ? error.message : "Não foi possível carregar os registros deste indicador.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [queryBase, pagina, buscaAplicada])

  const colunas = useMemo(() => {
    const conjunto = new Set<string>()
    dados?.registros.forEach((registro) => Object.keys(registro).forEach((chave) => conjunto.add(chave)))
    return Array.from(conjunto)
  }, [dados])

  function pesquisar(event: React.FormEvent) {
    event.preventDefault()
    setPagina(1)
    setBuscaAplicada(busca)
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1 overflow-x-hidden">
        <Topbar />
        <div className="space-y-5 p-4 sm:p-6 lg:p-8">
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <button onClick={() => router.back()} className="mb-4 inline-flex items-center gap-2 rounded-xl border border-[#17304d] bg-[#071226] px-4 py-2 text-sm text-cyan-200 transition hover:border-cyan-500/60 hover:bg-[#0a1b32]">
                <ArrowLeft size={16} /> Voltar à tela anterior
              </button>
              <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Rastreabilidade do indicador</p>
              <h1 className="mt-2 text-2xl font-bold sm:text-3xl">{titulo}</h1>
              <p className="mt-2 text-sm text-slate-400">{subtitulo}</p>
            </div>
            {dados && <div className="rounded-2xl border border-cyan-500/30 bg-cyan-950/20 px-5 py-4 text-right"><p className="text-xs uppercase tracking-wider text-slate-500">Total do recorte</p><strong className="mt-1 block text-3xl text-cyan-300">{dados.total_registros.toLocaleString("pt-BR")}</strong></div>}
          </header>

          <form onSubmit={pesquisar} className="flex max-w-2xl gap-2">
            <div className="relative min-w-0 flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={17}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar dentro deste recorte..." className="w-full rounded-xl border border-[#17304d] bg-[#071226] py-3 pl-10 pr-3 text-sm outline-none focus:border-cyan-500" /></div>
            <button className="rounded-xl bg-cyan-500 px-4 py-3 text-sm font-semibold text-slate-950">Buscar</button>
          </form>

          {erro && <div className="rounded-xl border border-red-500/50 bg-red-950/20 p-4 text-red-200">{erro}</div>}
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando registros individualizados...</div>}

          {!loading && dados && <>
            <section className="overflow-hidden rounded-2xl border border-[#17304d] bg-[#071226]">
              {dados.registros.length === 0 ? <div className="p-8 text-center text-slate-500">Nenhum registro encontrado neste recorte.</div> : <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-[#08162d] text-left text-xs uppercase tracking-wide text-slate-500"><tr>{colunas.map((chave) => <th key={chave} className="whitespace-nowrap px-4 py-3">{ROTULOS[chave] || chave.replaceAll("_", " ")}</th>)}</tr></thead><tbody className="divide-y divide-[#13203f]">{dados.registros.map((registro, indice) => <tr key={`${pagina}-${indice}`} className="align-top hover:bg-[#08162d]/60">{colunas.map((chave) => <td key={chave} className="max-w-[360px] whitespace-normal px-4 py-3 text-slate-300">{formatar(registro[chave], chave)}</td>)}</tr>)}</tbody></table></div>}
            </section>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#17304d] bg-[#071226] p-3 text-sm">
              <span className="text-slate-400">Página {dados.pagina} de {dados.total_paginas} · até {dados.limite} registros por página</span>
              <div className="flex gap-2"><button disabled={dados.pagina <= 1} onClick={() => setPagina((p) => Math.max(1, p - 1))} className="inline-flex items-center gap-1 rounded-lg border border-[#17304d] px-3 py-2 disabled:opacity-40"><ChevronLeft size={16}/> Anterior</button><button disabled={dados.pagina >= dados.total_paginas} onClick={() => setPagina((p) => p + 1)} className="inline-flex items-center gap-1 rounded-lg border border-[#17304d] px-3 py-2 disabled:opacity-40">Próxima <ChevronRight size={16}/></button></div>
            </div>
          </>}
        </div>
      </section>
    </main>
  )
}

function formatar(valor: unknown, chave: string) {
  if (valor === null || valor === undefined || valor === "") return "—"
  if (Array.isArray(valor)) return valor.join(", ") || "—"
  if (typeof valor === "object") return JSON.stringify(valor)
  if (typeof valor === "number" && (chave.includes("valor") || chave.includes("preco"))) return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
  if (typeof valor === "number") return valor.toLocaleString("pt-BR")
  return String(valor)
}
