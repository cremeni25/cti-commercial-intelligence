"use client"

import Image from "next/image"
import Link from "next/link"
import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import logoCTI from "@/assets/logo/Logo CTI - sem fundo.png"
import logoViena from "@/assets/logo/Logo Viena - transparente.png"
import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

type BootstrapForm = {
  nome: string
  email: string
  senha: string
  confirmarSenha: string
  empresa: string
  cargo: string
  territorio: string
  ddds: string
}

type PrimeiroAcessoStatus = {
  primeiro_acesso_pendente?: boolean
  cadastro_completo?: boolean
}

const bootstrapInicial: BootstrapForm = {
  nome: "",
  email: "",
  senha: "",
  confirmarSenha: "",
  empresa: "Viena SP",
  cargo: "CEO / Administrador Master",
  territorio: "Brasil",
  ddds: "011, 012, 013, 014, 015, 018",
}

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [verificando, setVerificando] = useState(true)
  const [bootstrapDisponivel, setBootstrapDisponivel] = useState(false)
  const [modoCadastro, setModoCadastro] = useState(false)
  const [cadastro, setCadastro] = useState<BootstrapForm>(bootstrapInicial)

  useEffect(() => {
    let ativo = true
    fetch(`${API_URL}/auth/bootstrap/status`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) return { disponivel: false }
        return response.json()
      })
      .then((data) => {
        if (ativo) setBootstrapDisponivel(Boolean(data.disponivel))
      })
      .catch(() => {
        if (ativo) setBootstrapDisponivel(false)
      })
      .finally(() => {
        if (ativo) setVerificando(false)
      })
    return () => { ativo = false }
  }, [])

  async function entrar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    setMensagem("")
    setEnviando(true)

    try {
      const supabase = getSupabaseClient()
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password: senha,
      })
      if (error) throw error
      if (!data.session?.access_token) throw new Error("Sessão autenticada não foi criada.")

      let statusPrimeiroAcesso: PrimeiroAcessoStatus | null = null
      try {
        const resposta = await fetch(`${API_URL}/governanca/primeiro-acesso/status`, {
          cache: "no-store",
          headers: { Authorization: `Bearer ${data.session.access_token}` },
        })
        if (resposta.ok) statusPrimeiroAcesso = await resposta.json()
      } catch {
        statusPrimeiroAcesso = null
      }

      if (
        statusPrimeiroAcesso?.primeiro_acesso_pendente ||
        statusPrimeiroAcesso?.cadastro_completo === false
      ) {
        router.replace("/primeiro-acesso")
      } else {
        router.replace("/dashboard")
      }
      router.refresh()
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível entrar no CTI.")
    } finally {
      setEnviando(false)
    }
  }

  async function recuperarSenha() {
    setErro("")
    setMensagem("")

    if (!email.trim()) {
      setErro("Informe o e-mail cadastrado antes de solicitar a recuperação de senha.")
      return
    }

    setEnviando(true)
    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/redefinir-senha`,
      })
      if (error) throw error
      setMensagem("Enviamos um link de recuperação para o e-mail informado. Abra a mensagem e defina uma nova senha.")
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível enviar o e-mail de recuperação.")
    } finally {
      setEnviando(false)
    }
  }

  async function criarPrimeiroAcesso(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    setMensagem("")

    if (cadastro.senha !== cadastro.confirmarSenha) {
      setErro("A confirmação da senha não corresponde.")
      return
    }

    setEnviando(true)
    try {
      const response = await fetch(`${API_URL}/auth/bootstrap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: cadastro.nome.trim(),
          email: cadastro.email.trim(),
          senha: cadastro.senha,
          empresa: cadastro.empresa.trim(),
          cargo: cadastro.cargo.trim(),
          territorio: cadastro.territorio.trim(),
          ddds: cadastro.ddds.split(",").map((item) => item.trim()).filter(Boolean),
        }),
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || "Não foi possível configurar o primeiro acesso.")

      setEmail(cadastro.email.trim())
      setSenha("")
      setBootstrapDisponivel(false)
      setModoCadastro(false)
      setMensagem("ADMIN_MASTER criado. Entre com o e-mail e a senha definidos.")
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível configurar o primeiro acesso.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#010817] px-5 py-8 text-white">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_78%_28%,rgba(0,104,255,0.16),transparent_26%),radial-gradient(circle_at_50%_10%,rgba(0,61,145,0.16),transparent_30%),linear-gradient(135deg,#010817_0%,#031126_52%,#020b18_100%)]" />
      <div aria-hidden="true" className="pointer-events-none absolute -right-24 top-24 h-[520px] w-[520px] rounded-full border border-blue-500/10 shadow-[0_0_120px_rgba(0,82,204,0.12)]" />
      <div aria-hidden="true" className="pointer-events-none absolute right-10 top-40 h-[380px] w-[380px] rounded-full border border-cyan-400/5" />

      <div className="relative z-10 flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <section className="w-full max-w-[760px] rounded-[30px] border border-[#24466f] bg-[linear-gradient(160deg,rgba(10,28,54,0.98),rgba(5,18,37,0.98))] px-6 py-7 shadow-[0_32px_90px_rgba(0,0,0,0.48),0_0_44px_rgba(0,102,255,0.08)] sm:px-10 sm:py-9">
          <div className="mb-8 text-center">
            <div className="flex flex-col items-center">
              <Image src={logoCTI} alt="CTI — Centro de Tecnologia e Inteligência Comercial" width={390} height={150} priority className="h-auto w-[300px] object-contain sm:w-[360px]" />

              <div className="mt-5 flex w-full max-w-md items-center gap-4">
                <span className="h-px flex-1 bg-gradient-to-r from-transparent via-[#45668c] to-[#45668c]" aria-hidden="true" />
                <span className="text-[10px] uppercase tracking-[0.4em] text-slate-400">Operação atendida</span>
                <span className="h-px flex-1 bg-gradient-to-l from-transparent via-[#45668c] to-[#45668c]" aria-hidden="true" />
              </div>
              <Image src={logoViena} alt="Refrigeração Viena" width={210} height={84} className="mt-3 h-auto w-[165px] object-contain sm:w-[185px]" />
            </div>

            <h1 className="mt-7 text-3xl font-bold tracking-tight text-white sm:text-4xl">{modoCadastro ? "Configuração inicial" : "Acesso ao sistema"}</h1>
            <p className="mt-2 text-sm text-slate-400 sm:text-base">
              {modoCadastro ? "Crie o primeiro ADMIN_MASTER responsável pela governança do CTI." : "Entre com as credenciais autorizadas do CTI."}
            </p>
          </div>

          {mensagem && <div className="mb-5 rounded-xl border border-emerald-800 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">{mensagem}</div>}
          {erro && <div className="mb-5 rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">{erro}</div>}

          {modoCadastro ? (
            <form onSubmit={criarPrimeiroAcesso} className="grid gap-4 sm:grid-cols-2">
              <Campo label="Nome completo" value={cadastro.nome} onChange={(value) => setCadastro({ ...cadastro, nome: value })} />
              <Campo label="E-mail" type="email" value={cadastro.email} onChange={(value) => setCadastro({ ...cadastro, email: value })} />
              <Campo label="Empresa" value={cadastro.empresa} onChange={(value) => setCadastro({ ...cadastro, empresa: value })} />
              <Campo label="Cargo institucional" value={cadastro.cargo} onChange={(value) => setCadastro({ ...cadastro, cargo: value })} />
              <Campo label="Território" value={cadastro.territorio} onChange={(value) => setCadastro({ ...cadastro, territorio: value })} />
              <Campo label="DDDs autorizados" value={cadastro.ddds} onChange={(value) => setCadastro({ ...cadastro, ddds: value })} />
              <Campo label="Senha" type="password" value={cadastro.senha} onChange={(value) => setCadastro({ ...cadastro, senha: value })} />
              <Campo label="Confirmar senha" type="password" value={cadastro.confirmarSenha} onChange={(value) => setCadastro({ ...cadastro, confirmarSenha: value })} />
              <div className="sm:col-span-2 rounded-xl border border-cyan-900/70 bg-cyan-950/20 px-4 py-3 text-xs leading-5 text-cyan-200">
                Perfil fixo: <strong>ADMIN_MASTER</strong>. Este cadastro será bloqueado automaticamente após a primeira criação.
              </div>
              <button disabled={enviando} className="sm:col-span-2 w-full rounded-xl border border-[#1374ff] bg-[linear-gradient(90deg,#064fc7,#086ee6,#0753c9)] px-4 py-3 font-semibold text-white shadow-[0_0_24px_rgba(0,102,255,0.22)] disabled:opacity-60">
                {enviando ? "Configurando..." : "Criar primeiro acesso"}
              </button>
              <button type="button" onClick={() => setModoCadastro(false)} className="sm:col-span-2 text-sm text-slate-400 hover:text-white">Voltar ao login</button>
            </form>
          ) : (
            <form onSubmit={entrar} className="space-y-5">
              <Campo label="E-mail" type="email" value={email} onChange={setEmail} />
              <Campo label="Senha" type="password" value={senha} onChange={setSenha} />
              <button disabled={enviando} className="w-full rounded-xl border border-[#1374ff] bg-[linear-gradient(90deg,#064fc7,#086ee6,#0753c9)] px-4 py-3 font-semibold text-white shadow-[0_0_24px_rgba(0,102,255,0.22)] transition hover:brightness-110 disabled:opacity-60">
                {enviando ? "Processando..." : "Entrar"}
              </button>
              <button type="button" disabled={enviando} onClick={recuperarSenha} className="w-full text-sm font-semibold text-[#1683ff] hover:text-cyan-300 disabled:opacity-60">
                Esqueci minha senha / definir primeira senha
              </button>
              <Link href="/solicitar-acesso" className="block w-full rounded-xl border border-[#24466f] bg-[#061126]/60 px-4 py-3 text-center text-sm font-semibold text-slate-400 transition hover:border-[#2f6aaa] hover:text-white">
                Solicitar acesso ao CTI
              </Link>
              {!verificando && bootstrapDisponivel && (
                <button type="button" onClick={() => { setErro(""); setModoCadastro(true) }} className="w-full rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-300 hover:bg-cyan-950/30">
                  Configurar primeiro acesso
                </button>
              )}
            </form>
          )}
        </section>
      </div>
    </main>
  )
}

function Campo({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block text-sm font-medium text-slate-200">{label}
      <input type={type} required autoComplete={type === "password" ? "current-password" : undefined} value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-[#315781] bg-[#041124]/90 px-4 py-3.5 text-white shadow-inner outline-none transition focus:border-[#1c7dff] focus:ring-1 focus:ring-[#1c7dff]/40" />
    </label>
  )
}
