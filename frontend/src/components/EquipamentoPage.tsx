"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getEquipamento, type EquipamentoEstrategico, type RankingItem } from "@/services/modulos-api"

export default function EquipamentoPage({ slug, fallbackTitulo }: { slug: string; fallbackTitulo: string }) {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dados, setDados] = useState<EquipamentoEstrategico | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    queueMicrotask(() => {
      if (!ativo) return
      setLoading(true)
      setErro("")
      getEquipamento(slug, queryString)
        .then((resultado) => { if (ativo) setDados(resultado) })
        .catch(() => { if (ativo) setErro("Não foi possível carregar as camadas estratégicas deste equipamento.") })
        .finally(() => { if (ativo) setLoading(false) })
    })
    return () => { ativo = false }
  }, [slug, queryString])

  const periodoExibido = periodo === "TODO_HISTORICO" ? "Todo o histórico" : periodo === "PERSONALIZADO" ? `${dataInicio || "?"} a ${dataFim || "?"}` : periodo.replaceAll("_", " ")

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-7 p-4 sm:p-6 lg:p-8">
          <header>
            <h1 className="text-3xl font-bold sm:text-4xl">{dados?.nome ?? fallbackTitulo}</h1>
            <p className="mt-2 text-sm text-slate-400">Leitura cruzada das três camadas comerciais do CTI, sem fundir registros nem transformar histórico em operação ativa.</p>
            <p className="mt-2 text-sm text-cyan-300">Contexto: {contextoAtual.label} • Período: {periodoExibido}</p>
          </header>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}

          {loading ? <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando realizado, histórico comercial e CRM em curso...</div> : dados && <>
            <section className="grid gap-4 xl:grid-cols-3">
              <Camada
                titulo="REALIZADO · ANFIR"
                descricao="O que já aconteceu no mercado confirmado."
                tom="cyan"
                kpis={[
                  ["Registros", numero(dados.realizado.total_registros)],
                  ["Valor realizado", moeda(dados.realizado.valor_total)],
                  ["Estados", numero(dados.realizado.estados.length)],
                ]}
              />
              <Camada
                titulo="HISTÓRICO COMERCIAL"
                descricao="Funil histórico 2023–2026 para consulta e comparação."
                tom="amber"
                kpis={[
                  ["Registros", numero(dados.historico_comercial.total_registros)],
                  ["Unidades", numero(dados.historico_comercial.total_unidades)],
                  ["Valor nominal", moeda(dados.historico_comercial.valor_nominal)],
                ]}
              />
              <Camada
                titulo="EM CURSO · CRM"
                descricao="Negociações operacionais abertas neste momento."
                tom="emerald"
                kpis={[
                  ["Oportunidades", numero(dados.em_curso.total_registros)],
                  ["Pipeline", moeda(dados.em_curso.valor_pipeline)],
                  ["Estados", numero(dados.em_curso.estados.length)],
                ]}
              />
            </section>

            <div className="rounded-xl border border-cyan-500/25 bg-cyan-950/10 p-4 text-sm text-cyan-100/80">
              As três camadas são correlacionadas visualmente, mas seus totais não são somados entre si. ANFIR continua sendo realizado; Histórico Comercial continua consulta histórica; CRM continua operação em curso.
            </div>

            <section className="grid gap-5 xl:grid-cols-3">
              <div className="space-y-5">
                <Ranking titulo="ANFIR · Estados" itens={dados.realizado.estados} vazio="Sem estado classificado no realizado." />
                <Ranking titulo="ANFIR · Implementadoras" itens={dados.realizado.implementadoras} vazio="Sem implementadora classificada no realizado." />
                <Ranking titulo="ANFIR · Empresas" itens={dados.realizado.empresas} vazio="Sem empresa classificada no realizado." />
              </div>
              <div className="space-y-5">
                <Ranking titulo="Histórico · Equipamentos" itens={dados.historico_comercial.equipamentos} vazio="Sem registro histórico desta família." />
                <Ranking titulo="Histórico · Status" itens={dados.historico_comercial.status} vazio="Sem status histórico desta família." />
                <Ranking titulo="Histórico · Implementadoras" itens={dados.historico_comercial.implementadoras} vazio="Sem implementadora histórica desta família." />
              </div>
              <div className="space-y-5">
                <Ranking titulo="CRM · Equipamentos" itens={dados.em_curso.equipamentos} vazio="Nenhuma negociação ativa desta família." />
                <Ranking titulo="CRM · Status" itens={dados.em_curso.status} vazio="Nenhuma negociação ativa desta família." />
                <Ranking titulo="CRM · Território" itens={dados.em_curso.estados.length ? dados.em_curso.estados : dados.em_curso.ddds} vazio="Nenhum território ativo desta família." />
              </div>
            </section>

            {dados.historico_comercial.nota_territorial && <p className="text-xs leading-5 text-slate-500">{dados.historico_comercial.nota_territorial}</p>}
          </>}
        </div>
      </section>
    </main>
  )
}

function Camada({ titulo, descricao, kpis, tom }: { titulo: string; descricao: string; kpis: [string, string][]; tom: "cyan" | "amber" | "emerald" }) {
  const cor = tom === "amber" ? "text-amber-300" : tom === "emerald" ? "text-emerald-300" : "text-cyan-300"
  return <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><p className={`text-xs font-semibold uppercase tracking-[.16em] ${cor}`}>{titulo}</p><p className="mt-2 text-sm text-slate-400">{descricao}</p><div className="mt-5 grid grid-cols-3 gap-2">{kpis.map(([rotulo, valor]) => <div key={rotulo} className="min-w-0 rounded-xl bg-[#08162d] p-3"><p className="text-[11px] text-slate-500">{rotulo}</p><strong className="mt-1 block break-words text-lg text-white">{valor}</strong></div>)}</div></section>
}

function Ranking({ titulo, itens, vazio }: { titulo: string; itens: RankingItem[]; vazio: string }) {
  return <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">{titulo}</h2>{itens.length === 0 ? <p className="mt-4 text-sm text-slate-500">{vazio}</p> : <div className="mt-4 space-y-2">{itens.slice(0, 10).map((item) => <div key={item.nome} className="flex items-center justify-between gap-4 rounded-xl bg-[#08162d] px-3 py-2.5 text-sm"><span className="min-w-0 truncate text-slate-300">{item.nome}</span><strong className="shrink-0 text-cyan-300">{item.quantidade_registros.toLocaleString("pt-BR")}</strong></div>)}</div>}</section>
}

function numero(valor: number) { return Number(valor || 0).toLocaleString("pt-BR") }
function moeda(valor: number) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }) }
