"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"
import { lerContextoOportunidade } from "@/lib/crm-opportunity"

type Registro = Record<string, unknown>
type Evento = {
  tipo: string
  data_hora?: string
  titulo?: string
  status?: string
  responsavel_id?: string
  registro: Registro
}
type Detalhes = {
  oportunidade: Registro & { id: string; cliente_nome?: string; titulo?: string; descricao?: string; status?: string; valor_estimado?: number; probabilidade?: number; data_fechamento_prevista?: string }
  resumo: { atividades: number; movimentacoes_pipeline: number; propostas: number; pedidos: number }
  eventos: Evento[]
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function percentual(valor: unknown) {
  const numero = Number(valor || 0)
  return `${Math.round(numero <= 1 ? numero * 100 : numero)}%`
}

function dataHora(valor?: string) {
  if (!valor) return "Data não informada"
  const data = new Date(valor)
  if (Number.isNaN(data.getTime())) return valor
  return data.toLocaleString("pt-BR")
}

export default function OportunidadeDetalhesPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [dados, setDados] = useState<Detalhes | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    if (!id) return
    let ativo = true
    setLoading(true)
    fetch(`${API_URL}/crm-visao/oportunidades/${id}/detalhes`, { cache: "no-store" })
      .then(async (response) => {
        const payload = await response.json().catch(() => null)
        if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar os detalhes.")
        return payload as Detalhes
      })
      .then((payload) => { if (ativo) setDados(payload) })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar a oportunidade.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [id])

  const contexto = useMemo(() => dados ? lerContextoOportunidade(dados.oportunidade) : null, [dados])

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <Link href="/oportunidades" className="text-sm font-semibold text-cyan-300">← Voltar para oportunidades</Link>
          <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Detalhes da oportunidade</p>
              <h1 className="mt-2 text-3xl font-bold">{dados?.oportunidade.titulo || "Oportunidade comercial"}</h1>
              <p className="mt-2 text-slate-400">{dados?.oportunidade.cliente_nome || "Cliente não identificado"}</p>
            </div>
            {dados && <span className="w-fit rounded-full border border-cyan-800 bg-cyan-950/30 px-4 py-2 text-sm text-cyan-200">{String(dados.oportunidade.status || "OPORTUNIDADE")}</span>}
          </div>
        </header>

        {loading && <Aviso>Carregando detalhes e histórico...</Aviso>}
        {erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-5 text-red-200">{erro}</div>}

        {dados && <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Kpi titulo="Valor estimado" valor={moeda(dados.oportunidade.valor_estimado)} />
            <Kpi titulo="Probabilidade" valor={percentual(dados.oportunidade.probabilidade)} />
            <Kpi titulo="Atividades" valor={String(dados.resumo.atividades)} />
            <Kpi titulo="Propostas / Pedidos" valor={`${dados.resumo.propostas} / ${dados.resumo.pedidos}`} />
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
            <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
              <h2 className="text-xl font-bold">Descrição comercial</h2>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-300">{contexto?.descricao || dados.oportunidade.descricao || "Nenhuma descrição registrada."}</p>
            </article>
            <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
              <h2 className="text-xl font-bold">Resumo operacional</h2>
              <dl className="mt-4 space-y-3 text-sm">
                <Linha label="Empresa" valor={String(dados.oportunidade.cliente_nome || "-")} />
                <Linha label="Produtos" valor={contexto?.equipamentos.join(", ") || "A definir"} />
                <Linha label="Quantidade" valor={String(contexto?.quantidade || 1)} />
                <Linha label="Território" valor={[contexto?.municipio, contexto?.uf].filter(Boolean).join(" / ") || "Não informado"} />
                <Linha label="Fechamento previsto" valor={String(dados.oportunidade.data_fechamento_prevista || "Não informado")} />
                <Linha label="Movimentações" valor={String(dados.resumo.movimentacoes_pipeline)} />
              </dl>
            </article>
          </section>

          <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div><h2 className="text-xl font-bold">Linha do tempo comercial</h2><p className="mt-1 text-sm text-slate-400">Atividades, alterações de etapa, propostas, pedidos e registros históricos.</p></div>
              <span className="text-sm text-cyan-300">{dados.eventos.length} evento(s)</span>
            </div>
            <div className="mt-6 space-y-3">
              {dados.eventos.length === 0 ? <p className="text-sm text-slate-500">Nenhum evento vinculado.</p> : dados.eventos.map((evento, indice) => <article key={`${evento.tipo}-${evento.data_hora}-${indice}`} className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div><span className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">{evento.tipo}</span><h3 className="mt-1 font-semibold text-white">{evento.titulo || evento.tipo}</h3></div>
                  <div className="text-left text-xs text-slate-500 sm:text-right"><p>{dataHora(evento.data_hora)}</p>{evento.status && <p className="mt-1 text-cyan-300">{evento.status}</p>}</div>
                </div>
              </article>)}
            </div>
          </section>
        </>}
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
function Linha({ label, valor }: { label: string; valor: string }) { return <div className="flex items-start justify-between gap-4 border-b border-[#13203f] pb-3 last:border-0"><dt className="text-slate-500">{label}</dt><dd className="text-right text-slate-200">{valor}</dd></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">{children}</div> }
