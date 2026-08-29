"use client"

import Link from "next/link"
import { FormEvent, Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { getSupabaseClient } from "@/core/database/supabase"
import { useI18n } from "@/core/i18n"
import LanguageSwitcher from "@/components/i18n/LanguageSwitcher"

export default function CrmLoginPage() {
  return (
    <Suspense fallback={<CrmLoginFallback />}>
      <CrmLoginContent />
    </Suspense>
  )
}

function CrmLoginContent() {
  const router = useRouter()
  const params = useSearchParams()
  const { t } = useI18n()
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [erro, setErro] = useState(params.get("acesso") === "negado" ? t("crmLogin.denied") : "")
  const [enviando, setEnviando] = useState(false)

  async function entrar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    setEnviando(true)
    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password: senha })
      if (error) throw error
      router.replace("/crm-app")
      router.refresh()
    } catch (error) {
      setErro(error instanceof Error ? error.message : t("crmLogin.failed"))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#020817] p-5 text-white">
      <section className="w-full max-w-md rounded-3xl border border-[#16325c] bg-[#091a33] p-6 shadow-2xl sm:p-8">
        <div className="mb-4 flex justify-end"><LanguageSwitcher /></div>
        <div className="mb-7 text-center">
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-cyan-400">CTI / Viena São Paulo</p>
          <h1 className="mt-3 text-3xl font-bold">{t("crmLogin.title")}</h1>
          <p className="mt-2 text-sm leading-6 text-slate-400">{t("crmLogin.subtitle")}</p>
        </div>
        {erro && <div className="mb-5 rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">{erro}</div>}
        <form onSubmit={entrar} className="space-y-5">
          <label className="block text-sm text-slate-300">{t("common.email")}<input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" /></label>
          <label className="block text-sm text-slate-300">{t("common.password")}<input type="password" required autoComplete="current-password" value={senha} onChange={(e) => setSenha(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" /></label>
          <button disabled={enviando} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{enviando ? t("crmLogin.entering") : t("crmLogin.enter")}</button>
        </form>
        <div className="mt-6 border-t border-[#16325c] pt-5 text-center">
          <p className="text-xs text-slate-500">{t("crmLogin.noAccess")}</p>
          <Link href="/solicitar-acesso?canal=CRM" className="mt-3 inline-flex rounded-xl border border-cyan-800 px-4 py-2 text-sm font-semibold text-cyan-300">{t("crmLogin.request")}</Link>
        </div>
      </section>
    </main>
  )
}

function CrmLoginFallback() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#020817] p-5 text-white">
      <div className="rounded-2xl border border-[#16325c] bg-[#091a33] px-6 py-5 text-sm text-slate-300">CTI CRM...</div>
    </main>
  )
}
