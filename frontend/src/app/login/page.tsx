"use client"

import { FormEvent, useState } from "react"
import { useRouter } from "next/navigation"
import { getSupabaseClient } from "@/core/database/supabase"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  async function entrar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    setEnviando(true)

    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password: senha })
      if (error) throw error
      router.replace("/dashboard")
      router.refresh()
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível entrar no CTI.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#020817] flex items-center justify-center p-6">
      <section className="w-full max-w-md rounded-3xl border border-[#16325c] bg-[#091a33] p-8 shadow-2xl">
        <div className="mb-8 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-400">CTI Inteligência Comercial</p>
          <h1 className="mt-3 text-3xl font-bold text-white">Acesso ao sistema</h1>
          <p className="mt-2 text-sm text-slate-400">Entre com as credenciais autorizadas do CTI.</p>
        </div>

        <form onSubmit={entrar} className="space-y-5">
          <label className="block text-sm text-slate-300">E-mail
            <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" />
          </label>
          <label className="block text-sm text-slate-300">Senha
            <input type="password" required autoComplete="current-password" value={senha} onChange={(e) => setSenha(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" />
          </label>
          {erro && <div className="rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">{erro}</div>}
          <button disabled={enviando} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">
            {enviando ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  )
}
