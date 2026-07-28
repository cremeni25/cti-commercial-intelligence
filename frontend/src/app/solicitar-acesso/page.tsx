"use client"

import Link from "next/link"
import { FormEvent, useState } from "react"
import { API_URL } from "@/lib/api"

type Formulario = {
  nome: string
  email: string
  telefone: string
  empresa: string
  cargo: string
  canal_solicitado: "PORTAL" | "CRM" | "AMBOS"
  observacoes: string
}

const inicial: Formulario = {
  nome: "",
  email: "",
  telefone: "",
  empresa: "Viena SP",
  cargo: "",
  canal_solicitado: "AMBOS",
  observacoes: "",
}

export default function SolicitarAcessoPage() {
  const [dados, setDados] = useState(inicial)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [enviando, setEnviando] = useState(false)

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    setMensagem("")
    setEnviando(true)

    try {
      const response = await fetch(`${API_URL}/auth/access-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || "Não foi possível registrar a solicitação.")
      setMensagem("Solicitação registrada. O ADMIN_MASTER fará a análise e, após aprovação, você receberá o convite para definir sua senha.")
      setDados(inicial)
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível registrar a solicitação.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#020817] px-4 py-8 text-white sm:px-6">
      <section className="mx-auto w-full max-w-2xl rounded-3xl border border-[#16325c] bg-[#091a33] p-6 shadow-2xl sm:p-8">
        <header className="mb-7 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-400">CTI / Viena São Paulo</p>
          <h1 className="mt-3 text-3xl font-bold">Solicitar acesso</h1>
          <p className="mt-2 text-sm leading-6 text-slate-400">O envio não libera acesso automático. A conta será criada somente após aprovação administrativa.</p>
        </header>

        {mensagem && <div className="mb-5 rounded-xl border border-emerald-800 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">{mensagem}</div>}
        {erro && <div className="mb-5 rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">{erro}</div>}

        <form onSubmit={enviar} className="grid gap-4 sm:grid-cols-2">
          <Campo label="Nome completo" value={dados.nome} onChange={(valor) => setDados({ ...dados, nome: valor })} />
          <Campo label="E-mail profissional" type="email" value={dados.email} onChange={(valor) => setDados({ ...dados, email: valor })} />
          <Campo label="Telefone" value={dados.telefone} onChange={(valor) => setDados({ ...dados, telefone: valor })} required={false} />
          <Campo label="Empresa" value={dados.empresa} onChange={(valor) => setDados({ ...dados, empresa: valor })} />
          <Campo label="Cargo ou função" value={dados.cargo} onChange={(valor) => setDados({ ...dados, cargo: valor })} />
          <label className="text-sm text-slate-300">Ambiente solicitado
            <select value={dados.canal_solicitado} onChange={(event) => setDados({ ...dados, canal_solicitado: event.target.value as Formulario["canal_solicitado"] })} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white">
              <option value="AMBOS">Portal CTI e App CRM</option>
              <option value="PORTAL">Somente Portal CTI</option>
              <option value="CRM">Somente App CRM</option>
            </select>
          </label>
          <label className="text-sm text-slate-300 sm:col-span-2">Observações
            <textarea value={dados.observacoes} onChange={(event) => setDados({ ...dados, observacoes: event.target.value })} rows={4} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" />
          </label>
          <button disabled={enviando} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60 sm:col-span-2">{enviando ? "Enviando solicitação..." : "Enviar solicitação de acesso"}</button>
        </form>

        <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm">
          <Link href="/login" className="text-cyan-300 hover:text-cyan-200">Voltar ao Portal CTI</Link>
          <Link href="/crm-app/login" className="text-cyan-300 hover:text-cyan-200">Voltar ao App CRM</Link>
        </div>
      </section>
    </main>
  )
}

function Campo({ label, value, onChange, type = "text", required = true }: { label: string; value: string; onChange: (valor: string) => void; type?: string; required?: boolean }) {
  return <label className="text-sm text-slate-300">{label}<input type={type} required={required} value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" /></label>
}
