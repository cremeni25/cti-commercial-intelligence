"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { getSupabaseClient } from "@/core/database/supabase"

export default function RedefinirSenhaPage() {
  const router = useRouter()
  const [senha, setSenha] = useState("")
  const [confirmarSenha, setConfirmarSenha] = useState("")
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [sessaoValida, setSessaoValida] = useState(false)
  const [verificando, setVerificando] = useState(true)

  useEffect(() => {
    const supabase = getSupabaseClient()
    let ativo = true

    async function verificarSessao() {
      const { data } = await supabase.auth.getSession()
      if (ativo) {
        setSessaoValida(Boolean(data.session))
        setVerificando(false)
      }
    }

    void verificarSessao()

    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      if (!ativo) return
      if (event === "PASSWORD_RECOVERY" || session) {
        setSessaoValida(true)
        setVerificando(false)
      }
    })

    return () => {
      ativo = false
      listener.subscription.unsubscribe()
    }
  }, [])

  async function atualizarSenha(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    setMensagem("")

    if (senha.length < 8) {
      setErro("A nova senha deve ter pelo menos 8 caracteres.")
      return
    }

    if (senha !== confirmarSenha) {
      setErro("A confirmação da senha não corresponde.")
      return
    }

    setEnviando(true)
    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.auth.updateUser({ password: senha })
      if (error) throw error

      await supabase.auth.signOut()
      setMensagem("Senha definida com sucesso. Você será direcionado para o login.")
      window.setTimeout(() => router.replace("/login"), 1500)
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível atualizar a senha.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#020817] flex items-center justify-center p-5">
      <section className="w-full max-w-md rounded-3xl border border-[#16325c] bg-[#091a33] p-6 shadow-2xl sm:p-8">
        <div className="mb-7 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-400">CTI Inteligência Comercial</p>
          <h1 className="mt-3 text-3xl font-bold text-white">Definir nova senha</h1>
          <p className="mt-2 text-sm text-slate-400">Crie a senha que será usada para entrar no CTI.</p>
        </div>

        {mensagem && <div className="mb-5 rounded-xl border border-emerald-800 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">{mensagem}</div>}
        {erro && <div className="mb-5 rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">{erro}</div>}

        {verificando ? (
          <div className="text-center text-sm text-slate-400">Validando o link de recuperação...</div>
        ) : !sessaoValida ? (
          <div className="space-y-4 text-center">
            <div className="rounded-xl border border-amber-800 bg-amber-950/30 px-4 py-3 text-sm text-amber-200">
              O link de recuperação é inválido ou expirou. Solicite um novo link na tela de login.
            </div>
            <button type="button" onClick={() => router.replace("/login")} className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">Voltar ao login</button>
          </div>
        ) : (
          <form onSubmit={atualizarSenha} className="space-y-5">
            <label className="block text-sm text-slate-300">Nova senha
              <input type="password" required minLength={8} autoComplete="new-password" value={senha} onChange={(event) => setSenha(event.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" />
            </label>
            <label className="block text-sm text-slate-300">Confirmar nova senha
              <input type="password" required minLength={8} autoComplete="new-password" value={confirmarSenha} onChange={(event) => setConfirmarSenha(event.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" />
            </label>
            <button disabled={enviando} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">
              {enviando ? "Salvando..." : "Salvar nova senha"}
            </button>
          </form>
        )}
      </section>
    </main>
  )
}
