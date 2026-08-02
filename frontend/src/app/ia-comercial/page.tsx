"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { API_URL } from "@/lib/api"

type Negocio = {
  oportunidade_id: string
  titulo: string
  cliente_nome: string
  etapa: string
  probabilidade: number
  valor: number
  valor_ponderado: number
  data_fechamento_prevista?: string | null
  proposta_numero?: string | null
  pedido_numero?: string | null
  encerrada?: boolean
}

type Recomendacao = {
  negocio: Negocio
  prioridade: number
  motivo: string
  acao: string
}

const ETAPAS_FINAIS = new Set(["FATURADO", "GANHO", "ENCERRADO", "PERDIDO", "CANCELADO"])

function moeda(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function percentual(valor: number) {
  const normalizado = valor <= 1 ? valor * 100 : valor
  return `${Math.round(normalizado)}%`
}

function diasAte(data?: string | null) {
  if (!data) return null
  const alvo = new Date(`${data.slice(0, 10)}T12:00:00`)
  if (Number.isNaN(alvo.getTime())) return null
  const hoje = new Date()
  hoje.setHours(12, 0, 0, 0)
  return Math.ceil((alvo.getTime() - hoje.getTime()) / 86_400_000)
}

function recomendar(negocio: Negocio): Recomendacao | null {
  if (negocio.encerrada || ETAPAS_FINAIS.has(negocio.etapa)) return null
  const dias = diasAte(negocio.data_fechamento_prevista)
  const probabilidade = negocio.probabilidade <= 1 ? negocio.probabilidade : negocio.probabilidade / 100
  let prioridade = Math.round(negocio.valor_ponderado / 10_000)
  let motivo = "Negociação aberta requer acompanhamento comercial."
  let acao = "Revisar o negócio e registrar a próxima atividade."

  if (dias !== null && dias < 0) {
    prioridade += 100 + Math.min(Math.abs(dias), 30)
    motivo = `Previsão de fechamento vencida há ${Math.abs(dias)} dia(s).`
    acao = "Atualizar a previsão e registrar contato imediato com o cliente."
  } else if (dias !== null && dias <= 7) {
    prioridade += 70
    motivo = `Fechamento previsto para os próximos ${dias} dia(s).`
    acao = negocio.etapa === "PROPOSTA" || negocio.etapa === "ACEITE"
      ? "Confirmar decisão, pendências e validade da proposta."
      : "Definir avanço formal para a próxima etapa."
  } else if (negocio.etapa === "PROPOSTA" && !negocio.proposta_numero) {
    prioridade += 60
    motivo = "Etapa de proposta sem documento vigente reconhecido pelo núcleo."
    acao = "Revisar o vínculo documental antes de prosseguir."
  } else if (negocio.etapa === "PEDIDO" && !negocio.pedido_numero) {
    prioridade += 60
    motivo = "Etapa de pedido sem pedido reconhecido pelo núcleo."
    acao = "Validar a conversão da proposta e o vínculo do pedido."
  } else if (probabilidade >= 0.7) {
    prioridade += 50
    motivo = "Alta probabilidade registrada em negócio ainda aberto."
    acao = "Concentrar esforço para formalizar o fechamento."
  } else if (!negocio.data_fechamento_prevista) {
    prioridade += 40
    motivo = "Negócio aberto sem previsão de fechamento."
    acao = "Definir uma previsão realista e a próxima atividade."
  }

  return { negocio, prioridade, motivo, acao }
}

export default function Page() {
  const { contextoAtual } = useOperationalContext()
  const [dados, setDados] = useState<Negocio[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    fetch(`${API_URL}/crm/nucleo-comercial`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Não foi possível carregar o núcleo comercial.")
        const payload = await response.json()
        return Array.isArray(payload) ? payload as Negocio[] : []
      })
      .then((payload) => { if (ativo) setDados(payload) })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar inteligência comercial.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [])

  const recomendacoes = useMemo(() => dados
    .map(recomendar)
    .filter((item): item is Recomendacao => Boolean(item))
    .sort((a, b) => b.prioridade - a.prioridade || b.negocio.valor_ponderado - a.negocio.valor_ponderado), [dados])

  const abertos = dados.filter((item) => !item.encerrada && !ETAPAS_FINAIS.has(item.etapa))
  const vencidos = abertos.filter((item) => (diasAte(item.data_fechamento_prevista) ?? 0) < 0 && Boolean(item.data_fechamento_prevista))
  const semPrevisao = abertos.filter((item) => !item.data_fechamento_prevista)
  const valorEmAberto = abertos.reduce((total, item) => total + Number(item.valor || 0), 0)
  const valorPonderado = abertos.reduce((total, item) => total + Number(item.valor_ponderado || 0), 0)

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Inteligência comercial auditável</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">IA Comercial</h1>
          <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-400">Prioridades e encaminhamentos derivados exclusivamente do núcleo CRM. Nenhuma recomendação altera dados ou substitui a decisão comercial humana.</p>
          <p className="mt-3 text-sm text-cyan-300">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}.</p>
        </header>

        {erro && <div className="rounded-xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <Kpi titulo="Negócios abertos" valor={String(abertos.length)} />
          <Kpi titulo="Previsões vencidas" valor={String(vencidos.length)} />
          <Kpi titulo="Sem previsão" valor={String(semPrevisao.length)} />
          <Kpi titulo="Valor em aberto" valor={moeda(valorEmAberto)} />
          <Kpi titulo="Valor ponderado" valor={moeda(valorPonderado)} />
        </section>

        <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
          <div><h2 className="text-xl font-bold">Fila de prioridade comercial</h2><p className="mt-1 text-sm text-slate-400">Ordenação por vencimento, proximidade do fechamento, integridade documental, probabilidade e valor ponderado.</p></div>
          {loading ? <p className="mt-6 text-slate-400">Analisando o núcleo comercial...</p> : recomendacoes.length === 0 ? <p className="mt-6 text-slate-500">Nenhum negócio aberto exige encaminhamento neste momento.</p> : <div className="mt-6 space-y-3">{recomendacoes.map(({ negocio, motivo, acao }, indice) => <article key={negocio.oportunidade_id} className="rounded-2xl border border-[#18345e] bg-[#091a33] p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Prioridade {indice + 1} · {negocio.etapa}</p><h3 className="mt-1 truncate text-lg font-bold">{negocio.cliente_nome} — {negocio.titulo}</h3><p className="mt-3 text-sm text-amber-200">{motivo}</p><p className="mt-2 text-sm text-slate-300"><strong>Próximo encaminhamento:</strong> {acao}</p></div>
              <div className="shrink-0 text-sm text-slate-400"><p>{moeda(negocio.valor)} · {percentual(negocio.probabilidade)}</p><p className="mt-1">Ponderado: {moeda(negocio.valor_ponderado)}</p><Link href={`/oportunidades/${negocio.oportunidade_id}`} className="mt-4 inline-flex rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300">Abrir oportunidade</Link></div>
            </div>
          </article>)}</div>}
        </section>

        <section className="rounded-2xl border border-cyan-900 bg-cyan-950/10 p-5 text-sm text-slate-300"><strong className="text-cyan-300">Critério de idoneidade:</strong> esta tela não inventa probabilidades, não prevê resultados por modelo opaco e não cria registros. Ela organiza fatos reconhecidos pelo núcleo comercial e explica o motivo de cada prioridade.</section>
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div>
}
