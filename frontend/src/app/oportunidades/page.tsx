"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
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
  data_fechamento_prevista?: string
  equipamento?: string
  linha_equipamentos?: string
  created_at?: string
}

function moeda(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function percentual(valor?: number) {
  const numero = Number(valor || 0)
  return Math.round(numero <= 1 ? numero * 100 : numero)
}

function inicioMesAtual() {
  const agora = new Date()
  return `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, "0")}-01`
}

function fimMesAtual() {
  const agora = new Date()
  return new Date(agora.getFullYear(), agora.getMonth() + 1, 0).toISOString().slice(0, 10)
}

export default function OportunidadesPage() {
  const [dados, setDados] = useState<Oportunidade[]>([])
  const [inicio, setInicio] = useState(inicioMesAtual)
  const [fim, setFim] = useState(fimMesAtual)
  const [busca, setBusca] = useState("")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")
    fetch(`${API_URL}/crm-visao/oportunidades?inicio=${inicio}&fim=${fim}`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Falha ao carregar oportunidades")
        return response.json() as Promise<Oportunidade[]>
      })
      .then((registros) => { if (ativo) setDados(Array.isArray(registros) ? registros : []) })
      .catch(() => { if (ativo) setErro("Não foi possível carregar as oportunidades do período.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [inicio, fim])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return dados
    return dados.filter((item) => `${item.cliente_nome} ${item.titulo} ${item.status} ${item.equipamento || ""} ${item.linha_equipamentos || ""}`.toLocaleLowerCase("pt-BR").includes(termo))
  }, [busca, dados])

  const abertas = dados.filter((item) => !["GANHO", "PERDIDO", "CANCELADO"].includes(String(item.status || "").toUpperCase()))
  const valorTotal = abertas.reduce((total, item) => total + Number(item.valor_estimado || 0), 0)
  const valorPonderado = abertas.reduce((total, item) => total + Number(item.valor_estimado || 0) * (percentual(item.probabilidade) / 100), 0)

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold sm:text-4xl">CRM • Oportunidades</h1>
              <p className="mt-2 text-gray-400">Uma linha por oportunidade. As descrições completas permanecem na tela de detalhes.</p>
            </div>
            <Link href="/crm-app/oportunidades/nova" className="rounded-xl bg-cyan-500 px-5 py-3 text-center font-semibold text-slate-950">Nova oportunidade</Link>
          </header>

          <section className="grid gap-4 rounded-2xl border border-[#13203f] bg-[#071226] p-5 md:grid-cols-2 xl:grid-cols-[1fr_1fr_2fr_auto]">
            <CampoData label="Início" value={inicio} onChange={setInicio} />
            <CampoData label="Fim" value={fim} onChange={setFim} />
            <label className="text-sm text-slate-300">Buscar<input value={busca} onChange={(event) => setBusca(event.target.value)} placeholder="Empresa, oportunidade, produto ou etapa" className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" /></label>
            <button type="button" onClick={() => { setInicio(inicioMesAtual()); setFim(fimMesAtual()) }} className="self-end rounded-xl border border-cyan-700 px-4 py-3 text-cyan-300">Mês atual</button>
          </section>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Kpi titulo="Registros no período" valor={dados.length.toLocaleString("pt-BR")} />
            <Kpi titulo="Oportunidades abertas" valor={abertas.length.toLocaleString("pt-BR")} />
            <Kpi titulo="Pipeline total" valor={moeda(valorTotal)} />
            <Kpi titulo="Pipeline ponderado" valor={moeda(valorPonderado)} />
          </section>

          <div className="overflow-x-auto rounded-2xl border border-[#13203f] bg-[#091a33]">
            {loading ? <Aviso>Carregando oportunidades...</Aviso> : filtrados.length === 0 ? <Aviso>Nenhuma oportunidade encontrada no período.</Aviso> : (
              <table className="min-w-[1050px] w-full text-left text-sm">
                <thead className="bg-[#061326] text-xs uppercase text-slate-500">
                  <tr><th className="px-5 py-4">Empresa</th><th className="px-5 py-4">Oportunidade</th><th className="px-5 py-4">Produto</th><th className="px-5 py-4">Valor</th><th className="px-5 py-4">Chance</th><th className="px-5 py-4">Etapa</th><th className="px-5 py-4">Previsão</th><th className="px-5 py-4">Ação</th></tr>
                </thead>
                <tbody className="divide-y divide-[#13203f]">
                  {filtrados.map((item) => {
                    const contexto = lerContextoOportunidade(item)
                    return <tr key={item.id} className="align-middle text-slate-200">
                      <td className="px-5 py-4 font-semibold text-cyan-300">{item.cliente_nome}</td>
                      <td className="px-5 py-4 font-medium">{item.titulo}</td>
                      <td className="px-5 py-4">{contexto.equipamentos.join(", ") || item.equipamento || item.linha_equipamentos || "A definir"}</td>
                      <td className="px-5 py-4 text-emerald-300">{moeda(Number(item.valor_estimado || 0))}</td>
                      <td className="px-5 py-4">{percentual(item.probabilidade)}%</td>
                      <td className="px-5 py-4">{item.status}</td>
                      <td className="px-5 py-4">{item.data_fechamento_prevista ? new Date(`${item.data_fechamento_prevista}T12:00:00`).toLocaleDateString("pt-BR") : "—"}</td>
                      <td className="px-5 py-4"><Link href={`/oportunidades/${item.id}`} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300">Ver detalhes</Link></td>
                    </tr>
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}

function CampoData({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="text-sm text-slate-300">{label}<input type="date" value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" /></label>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-gray-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-400">{valor}</p></div>
}

function Aviso({ children }: { children: React.ReactNode }) {
  return <div className="p-10 text-gray-300">{children}</div>
}
