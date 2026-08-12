"use client"

import { useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Download, FileText } from "lucide-react"
import { getSupabaseClient } from "@/core/database/supabase"

type DadoGrafico = { label: string; valor: number; unidade?: string }
type Artefato = {
  tipo: "GRAFICO" | "RELATORIO_PDF" | string
  formato?: string
  titulo?: string
  dados?: DadoGrafico[]
  status?: string
  mensagem?: string
}

type Props = {
  mensagemId?: string
  artefatos?: Artefato[]
}

const CORES_PIZZA = ["#06b6d4", "#22d3ee", "#0891b2", "#67e8f9", "#0e7490", "#a5f3fc", "#155e75", "#164e63"]

async function baixarAutenticado(url: string, nomeFallback: string) {
  const supabase = getSupabaseClient()
  const { data } = await supabase.auth.getSession()
  let token = data.session?.access_token
  if (!token) {
    const renovada = await supabase.auth.refreshSession()
    token = renovada.data.session?.access_token
  }
  if (!token) throw new Error("Sessão autenticada não encontrada.")

  const resposta = await fetch(url, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resposta.ok) {
    const detalhe = await resposta.json().catch(() => null)
    throw new Error(detalhe?.detail || "Não foi possível baixar o artefato.")
  }
  const blob = await resposta.blob()
  const disposicao = resposta.headers.get("content-disposition") || ""
  const match = disposicao.match(/filename="?([^";]+)"?/i)
  const nome = match?.[1] || nomeFallback
  const href = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = href
  link.download = nome
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(href)
}

function VisualizacaoGrafico({ formato, dados }: { formato: string; dados: DadoGrafico[] }) {
  const tooltip = {
    background: "#071427",
    border: "1px solid #164e63",
    borderRadius: 10,
  }

  if (formato === "LINE") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={dados} margin={{ top: 16, right: 24, bottom: 20, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.18} />
          <XAxis dataKey="label" tick={{ fill: "#cbd5e1", fontSize: 11 }} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <Tooltip contentStyle={tooltip} labelStyle={{ color: "#e2e8f0" }} />
          <Line type="monotone" dataKey="valor" stroke="#06b6d4" strokeWidth={3} dot={{ r: 5 }} activeDot={{ r: 7 }} />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  if (formato === "PIE") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={dados} dataKey="valor" nameKey="label" cx="50%" cy="46%" outerRadius="72%" label>
            {dados.map((item, indice) => (
              <Cell key={`${item.label}-${indice}`} fill={CORES_PIZZA[indice % CORES_PIZZA.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltip} labelStyle={{ color: "#e2e8f0" }} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dados} layout="vertical" margin={{ top: 8, right: 32, bottom: 8, left: 24 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.18} />
        <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <YAxis dataKey="label" type="category" width={110} tick={{ fill: "#cbd5e1", fontSize: 11 }} />
        <Tooltip contentStyle={tooltip} labelStyle={{ color: "#e2e8f0" }} />
        <Bar dataKey="valor" fill="#06b6d4" radius={[0, 7, 7, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function IaArtefatos({ mensagemId, artefatos }: Props) {
  const [baixando, setBaixando] = useState("")
  const [erro, setErro] = useState("")
  if (!mensagemId || !artefatos?.length) return null

  const id = mensagemId
  const grafico = artefatos.find((item) => item.tipo === "GRAFICO")
  const relatorio = artefatos.find((item) => item.tipo === "RELATORIO_PDF")
  const dados = Array.isArray(grafico?.dados) ? grafico.dados : []
  const formato = String(grafico?.formato || "BAR").toUpperCase()

  async function baixar(tipo: "grafico" | "relatorio") {
    setErro("")
    setBaixando(tipo)
    try {
      if (tipo === "grafico") {
        await baixarAutenticado(
          `/api/crm-proxy/ia-comercial-cti/artefatos/${id}/grafico.svg`,
          `cti-grafico-${id.slice(0, 8)}.svg`,
        )
      } else {
        await baixarAutenticado(
          `/api/crm-proxy/ia-comercial-cti/artefatos/${id}/relatorio.pdf`,
          `cti-relatorio-${id.slice(0, 8)}.pdf`,
        )
      }
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao baixar artefato.")
    } finally {
      setBaixando("")
    }
  }

  return (
    <div className="mt-4 space-y-3 border-t border-[#18345e] pt-4">
      {grafico && dados.length > 0 ? (
        <section className="rounded-2xl border border-cyan-900/70 bg-[#061126] p-3 sm:p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-400">Gráfico IA-009 · {formato}</p>
              <h3 className="mt-1 text-sm font-semibold text-slate-100 sm:text-base">{grafico.titulo || "Análise gráfica CTI"}</h3>
            </div>
            <button
              type="button"
              onClick={() => void baixar("grafico")}
              disabled={baixando === "grafico"}
              className="inline-flex items-center gap-2 rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-950/50 disabled:opacity-50"
            >
              <Download size={15} /> {baixando === "grafico" ? "Baixando..." : "Baixar SVG"}
            </button>
          </div>
          <div className="h-[320px] w-full sm:h-[380px]">
            <VisualizacaoGrafico formato={formato} dados={dados} />
          </div>
        </section>
      ) : grafico?.status === "SEM_SERIE_NUMERICA" ? (
        <div className="rounded-xl border border-amber-900/70 bg-amber-950/20 p-3 text-xs text-amber-200">
          {grafico.mensagem || "Não há série numérica suficiente para gerar o gráfico sem inventar dados."}
        </div>
      ) : null}

      {relatorio ? (
        <button
          type="button"
          onClick={() => void baixar("relatorio")}
          disabled={baixando === "relatorio"}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-100 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-white disabled:opacity-50"
        >
          <FileText size={17} /> {baixando === "relatorio" ? "Gerando download..." : "Baixar relatório PDF"}
        </button>
      ) : null}
      {erro ? <p className="text-xs text-red-300">{erro}</p> : null}
    </div>
  )
}
