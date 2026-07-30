"use client"

import Link from "next/link"
import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
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
    <main className="min-h-screen bg-[#020817] flex items-center justify-center p-5">
      <section className="w-full max-w-xl rounded-3xl border border-[#16325c] bg-[#091a33] p-6 shadow-2xl sm:p-8">
        <div className="mb-7 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-400">CTI Inteligência Comercial</p>
          <h1 className="mt-3 text-3xl font-bold text-white">{modoCadastro ? "Configuração inicial" : "Acesso ao sistema"}</h1>
          <p className="mt-2 text-sm text-slate-400">
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
            <button disabled={enviando} className="sm:col-span-2 w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">
              {enviando ? "Configurando..." : "Criar primeiro acesso"}
            </button>
            <button type="button" onClick={() => setModoCadastro(false)} className="sm:col-span-2 text-sm text-slate-400 hover:text-white">Voltar ao login</button>
          </form>
        ) : (
          <form onSubmit={entrar} className="space-y-5">
            <Campo label="E-mail" type="email" value={email} onChange={setEmail} />
            <Campo label="Senha" type="password" value={senha} onChange={setSenha} />
            <button disabled={enviando} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">
              {enviando ? "Processando..." : "Entrar"}
            </button>
            <button type="button" disabled={enviando} onClick={recuperarSenha} className="w-full text-sm font-semibold text-cyan-300 hover:text-cyan-200 disabled:opacity-60">
              Esqueci minha senha / definir primeira senha
            </button>
            <Link href="/solicitar-acesso" className="block w-full rounded-xl border border-[#1d3b67] px-4 py-3 text-center text-sm font-semibold text-slate-300 hover:border-cyan-700 hover:text-cyan-200">
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
    </main>
  )
}

function Campo({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block text-sm text-slate-300">{label}
      <input type={type} required autoComplete={type === "password" ? "current-password" : undefined} value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" />
    </label>
  )
}
