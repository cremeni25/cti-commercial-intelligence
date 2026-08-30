"use client"

import Link from "next/link"
import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"
import { useI18n } from "@/core/i18n"
import LanguageSwitcher from "@/components/i18n/LanguageSwitcher"

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

const ui = {
  "pt-BR": {
    brand: "CTI Inteligência Comercial",
    sessionMissing: "Sessão autenticada não foi criada.",
    signInFailed: "Não foi possível entrar no CTI.",
    emailRequired: "Informe o e-mail cadastrado antes de solicitar a recuperação de senha.",
    recoverySent: "Enviamos um link de recuperação para o e-mail informado. Abra a mensagem e defina uma nova senha.",
    recoveryFailed: "Não foi possível enviar o e-mail de recuperação.",
    passwordMismatch: "A confirmação da senha não corresponde.",
    bootstrapFailed: "Não foi possível configurar o primeiro acesso.",
    bootstrapCreated: "ADMIN_MASTER criado. Entre com o e-mail e a senha definidos.",
    fullName: "Nome completo",
    company: "Empresa",
    role: "Cargo institucional",
    territory: "Território",
    ddds: "DDDs autorizados",
    confirmPassword: "Confirmar senha",
    fixedProfile: "Perfil fixo:",
    fixedProfileDetail: "Este cadastro será bloqueado automaticamente após a primeira criação.",
    configuring: "Configurando...",
    createFirstAccess: "Criar primeiro acesso",
    backToLogin: "Voltar ao login",
  },
  en: {
    brand: "CTI Commercial Intelligence",
    sessionMissing: "The authenticated session could not be created.",
    signInFailed: "We couldn't sign you in to CTI.",
    emailRequired: "Enter your registered email before requesting password recovery.",
    recoverySent: "We sent a recovery link to the email provided. Open the message and set a new password.",
    recoveryFailed: "We couldn't send the password recovery email.",
    passwordMismatch: "Password confirmation does not match.",
    bootstrapFailed: "We couldn't configure the initial access.",
    bootstrapCreated: "ADMIN_MASTER created. Sign in with the email and password you defined.",
    fullName: "Full name",
    company: "Company",
    role: "Institutional role",
    territory: "Territory",
    ddds: "Authorized area codes",
    confirmPassword: "Confirm password",
    fixedProfile: "Fixed profile:",
    fixedProfileDetail: "This registration will be automatically locked after the first account is created.",
    configuring: "Configuring...",
    createFirstAccess: "Create first access",
    backToLogin: "Back to sign in",
  },
  es: {
    brand: "CTI Inteligencia Comercial",
    sessionMissing: "No se pudo crear la sesión autenticada.",
    signInFailed: "No fue posible ingresar a CTI.",
    emailRequired: "Ingrese el correo electrónico registrado antes de solicitar la recuperación de contraseña.",
    recoverySent: "Enviamos un enlace de recuperación al correo informado. Abra el mensaje y defina una nueva contraseña.",
    recoveryFailed: "No fue posible enviar el correo de recuperación.",
    passwordMismatch: "La confirmación de la contraseña no coincide.",
    bootstrapFailed: "No fue posible configurar el primer acceso.",
    bootstrapCreated: "ADMIN_MASTER creado. Ingrese con el correo y la contraseña definidos.",
    fullName: "Nombre completo",
    company: "Empresa",
    role: "Cargo institucional",
    territory: "Territorio",
    ddds: "Códigos de área autorizados",
    confirmPassword: "Confirmar contraseña",
    fixedProfile: "Perfil fijo:",
    fixedProfileDetail: "Este registro se bloqueará automáticamente después de crear la primera cuenta.",
    configuring: "Configurando...",
    createFirstAccess: "Crear primer acceso",
    backToLogin: "Volver al acceso",
  },
} as const

export default function LoginPage() {
  const router = useRouter()
  const { t, locale } = useI18n()
  const tx = ui[locale]
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
      if (!data.session?.access_token) throw new Error(tx.sessionMissing)

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

      if (statusPrimeiroAcesso?.primeiro_acesso_pendente || statusPrimeiroAcesso?.cadastro_completo === false) {
        router.replace("/primeiro-acesso")
      } else {
        router.replace("/dashboard")
      }
      router.refresh()
    } catch (error) {
      setErro(error instanceof Error ? error.message : tx.signInFailed)
    } finally {
      setEnviando(false)
    }
  }

  async function recuperarSenha() {
    setErro("")
    setMensagem("")
    if (!email.trim()) {
      setErro(tx.emailRequired)
      return
    }
    setEnviando(true)
    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/redefinir-senha`,
      })
      if (error) throw error
      setMensagem(tx.recoverySent)
    } catch (error) {
      setErro(error instanceof Error ? error.message : tx.recoveryFailed)
    } finally {
      setEnviando(false)
    }
  }

  async function criarPrimeiroAcesso(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    setMensagem("")
    if (cadastro.senha !== cadastro.confirmarSenha) {
      setErro(tx.passwordMismatch)
      return
    }
    setEnviando(true)
    try {
      const response = await fetch(`${API_URL}/auth/bootstrap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: cadastro.nome.trim(), email: cadastro.email.trim(), senha: cadastro.senha,
          empresa: cadastro.empresa.trim(), cargo: cadastro.cargo.trim(), territorio: cadastro.territorio.trim(),
          ddds: cadastro.ddds.split(",").map((item) => item.trim()).filter(Boolean),
        }),
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || tx.bootstrapFailed)
      setEmail(cadastro.email.trim())
      setSenha("")
      setBootstrapDisponivel(false)
      setModoCadastro(false)
      setMensagem(tx.bootstrapCreated)
    } catch (error) {
      setErro(error instanceof Error ? error.message : tx.bootstrapFailed)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#020817] flex items-center justify-center p-5">
      <section className="w-full max-w-xl rounded-3xl border border-[#16325c] bg-[#091a33] p-6 shadow-2xl sm:p-8">
        <div className="mb-4 flex justify-end"><LanguageSwitcher /></div>
        <div className="mb-7 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-400">{tx.brand}</p>
          <h1 className="mt-3 text-3xl font-bold text-white">{modoCadastro ? t("login.initialSetup") : t("login.title")}</h1>
          <p className="mt-2 text-sm text-slate-400">{modoCadastro ? t("login.initialSetupDescription") : t("login.subtitle")}</p>
        </div>

        {mensagem && <div className="mb-5 rounded-xl border border-emerald-800 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">{mensagem}</div>}
        {erro && <div className="mb-5 rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">{erro}</div>}

        {modoCadastro ? (
          <form onSubmit={criarPrimeiroAcesso} className="grid gap-4 sm:grid-cols-2">
            <Campo label={tx.fullName} value={cadastro.nome} onChange={(value) => setCadastro({ ...cadastro, nome: value })} />
            <Campo label={t("common.email")} type="email" value={cadastro.email} onChange={(value) => setCadastro({ ...cadastro, email: value })} />
            <Campo label={tx.company} value={cadastro.empresa} onChange={(value) => setCadastro({ ...cadastro, empresa: value })} />
            <Campo label={tx.role} value={cadastro.cargo} onChange={(value) => setCadastro({ ...cadastro, cargo: value })} />
            <Campo label={tx.territory} value={cadastro.territorio} onChange={(value) => setCadastro({ ...cadastro, territorio: value })} />
            <Campo label={tx.ddds} value={cadastro.ddds} onChange={(value) => setCadastro({ ...cadastro, ddds: value })} />
            <Campo label={t("common.password")} type="password" value={cadastro.senha} onChange={(value) => setCadastro({ ...cadastro, senha: value })} />
            <Campo label={tx.confirmPassword} type="password" value={cadastro.confirmarSenha} onChange={(value) => setCadastro({ ...cadastro, confirmarSenha: value })} />
            <div className="sm:col-span-2 rounded-xl border border-cyan-900/70 bg-cyan-950/20 px-4 py-3 text-xs leading-5 text-cyan-200">{tx.fixedProfile} <strong>ADMIN_MASTER</strong>. {tx.fixedProfileDetail}</div>
            <button disabled={enviando} className="sm:col-span-2 w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{enviando ? tx.configuring : tx.createFirstAccess}</button>
            <button type="button" onClick={() => setModoCadastro(false)} className="sm:col-span-2 text-sm text-slate-400 hover:text-white">{tx.backToLogin}</button>
          </form>
        ) : (
          <form onSubmit={entrar} className="space-y-5">
            <Campo label={t("common.email")} type="email" value={email} onChange={setEmail} />
            <Campo label={t("common.password")} type="password" value={senha} onChange={setSenha} />
            <button disabled={enviando} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{enviando ? t("login.processing") : t("common.enter")}</button>
            <button type="button" disabled={enviando} onClick={recuperarSenha} className="w-full text-sm font-semibold text-cyan-300 hover:text-cyan-200 disabled:opacity-60">{t("login.forgot")}</button>
            <Link href="/solicitar-acesso" className="block w-full rounded-xl border border-[#1d3b67] px-4 py-3 text-center text-sm font-semibold text-slate-300 hover:border-cyan-700 hover:text-cyan-200">{t("login.requestAccess")}</Link>
            {!verificando && bootstrapDisponivel && (
              <button type="button" onClick={() => { setErro(""); setModoCadastro(true) }} className="w-full rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-300 hover:bg-cyan-950/30">{t("login.initialSetup")}</button>
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
