"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

type StatusPrimeiroAcesso = {
  primeiro_acesso_pendente: boolean
  cadastro_completo: boolean
  tipo_usuario?: string
}

export default function PrimeiroAcessoPage() {
  const router = useRouter()
  const [status, setStatus] = useState<StatusPrimeiroAcesso | null>(null)
  const [senha, setSenha] = useState("")
  const [confirmacao, setConfirmacao] = useState("")
  const [nome, setNome] = useState("")
  const [telefone, setTelefone] = useState("")
  const [cargo, setCargo] = useState("")
  const [departamento, setDepartamento] = useState("")
  const [territorio, setTerritorio] = useState("Viena SP")
  const [ddds, setDdds] = useState("")
  const [erro, setErro] = useState("")
  const [salvando, setSalvando] = useState(false)

  async function tokenAtual() {
    const supabase = getSupabaseClient()
    const { data, error } = await supabase.auth.getSession()
    if (error || !data.session?.access_token) throw new Error("Sessão autenticada não encontrada.")
    return data.session.access_token
  }

  async function carregarStatus() {
    try {
      const token = await tokenAtual()
      const response = await fetch(`${API_URL}/governanca/primeiro-acesso/status`, {
        cache: "no-store",
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) throw new Error("Não foi possível verificar o primeiro acesso.")
      const dados = await response.json()
      setStatus(dados)
      if (!dados.primeiro_acesso_pendente && dados.cadastro_completo) router.replace("/dashboard")
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Falha ao verificar o primeiro acesso.")
    }
  }

  useEffect(() => {
    void carregarStatus()
  }, [])

  async function concluir(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setErro("")
    if (senha.length < 8) return setErro("A nova senha deve possuir ao menos 8 caracteres.")
    if (senha !== confirmacao) return setErro("A confirmação da senha não corresponde.")

    setSalvando(true)
    try {
      const supabase = getSupabaseClient()
      const { error: senhaErro } = await supabase.auth.updateUser({ password: senha })
      if (senhaErro) throw senhaErro

      const token = await tokenAtual()
      const response = await fetch(`${API_URL}/governanca/primeiro-acesso/concluir`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          cadastro: {
            nome: nome.trim(),
            telefone: telefone.trim(),
            cargo: cargo.trim(),
            departamento: departamento.trim() || null,
            territorio: territorio.trim() || null,
            ddds: ddds.split(",").map((item) => item.trim()).filter(Boolean),
          },
        }),
      })
      const detalhe = await response.json().catch(() => null)
      if (!response.ok) throw new Error(detalhe?.detail || "Não foi possível concluir o cadastro.")

      router.replace("/dashboard")
      router.refresh()
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível concluir o primeiro acesso.")
    } finally {
      setSalvando(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#020817] p-5 text-white">
      <section className="mx-auto max-w-3xl rounded-3xl border border-[#16325c] bg-[#091a33] p-6 shadow-2xl sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-400">CTI Primeiro acesso</p>
        <h1 className="mt-3 text-3xl font-bold">Defina sua senha e complete o cadastro</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">A navegação normal será liberada somente depois da substituição da senha temporária e da conclusão dos dados funcionais.</p>

        {!status && !erro && <p className="mt-6 text-slate-400">Verificando acesso...</p>}
        {erro && <div className="mt-6 rounded-xl border border-red-800 bg-red-950/30 px-4 py-3 text-sm text-red-200">{erro}</div>}

        {status && (
          <form onSubmit={concluir} className="mt-7 grid gap-4 sm:grid-cols-2">
            <Campo label="Nova senha" type="password" value={senha} onChange={setSenha} required />
            <Campo label="Confirmar nova senha" type="password" value={confirmacao} onChange={setConfirmacao} required />
            <Campo label="Nome completo" value={nome} onChange={setNome} required />
            <Campo label="Telefone" value={telefone} onChange={setTelefone} required />
            <Campo label="Cargo/função formal" value={cargo} onChange={setCargo} required />
            <Campo label="Departamento" value={departamento} onChange={setDepartamento} />
            <Campo label="Território" value={territorio} onChange={setTerritorio} />
            <Campo label="DDDs autorizados" value={ddds} onChange={setDdds} placeholder="011, 012, 013" />
            <div className="sm:col-span-2 rounded-xl border border-cyan-900/70 bg-cyan-950/20 px-4 py-3 text-sm text-cyan-200">Função de acesso definida pelo ADMIN_MASTER: <strong>{status.tipo_usuario || "CTI"}</strong></div>
            <button disabled={salvando} className="sm:col-span-2 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60">{salvando ? "Concluindo..." : "Concluir primeiro acesso"}</button>
          </form>
        )}
      </section>
    </main>
  )
}

function Campo({ label, value, onChange, type = "text", placeholder, required = false }: { label: string; value: string; onChange: (value: string) => void; type?: string; placeholder?: string; required?: boolean }) {
  return <label className="text-sm text-slate-300">{label}<input value={value} onChange={(e) => onChange(e.target.value)} type={type} placeholder={placeholder} required={required} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" /></label>
}