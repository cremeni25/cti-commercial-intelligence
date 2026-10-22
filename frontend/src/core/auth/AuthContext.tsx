"use client"

import { createContext, useContext, useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { getSupabaseClient } from "../database/supabase"
import { UsuarioCTI } from "./types"
import { buscarUsuarioAtual } from "./auth.service"
import { CHAVE_SAIDA_CTI, obterSessaoCTI, registrarSessaoCTI, sessaoCTIBloqueada } from "./session"
import { rotaAutorizadaCTI } from "@/core/rbac/route-access"
import type { Session } from "@supabase/supabase-js"
import { possuiContextoFeiras, recuperarContextoFeiras, bloquearCofre } from "@/lib/feiras-cofre"

interface AuthContextType {
  usuario: UsuarioCTI | null
  loading: boolean
  sair: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({ usuario: null, loading: true, sair: async () => undefined })
const ROTAS_PUBLICAS = new Set(["/", "/login", "/redefinir-senha", "/crm-app/login", "/solicitar-acesso"])
const ROTA_PORTAL_PRINCIPAL = "/mapa-estrategico"
const rotaInicial = (perfil: UsuarioComCanais) => ["AUTORIZADO_CARRIER","GESTOR_AUTORIZADO_CARRIER"].includes(String(perfil.tipo_usuario).toUpperCase()) ? "/crm-app/feiras" : perfil.acesso_portal === false && perfil.acesso_crm !== false ? "/crm-app" : ROTA_PORTAL_PRINCIPAL

type UsuarioComCanais = UsuarioCTI & { acesso_portal?: boolean; acesso_crm?: boolean; status_acesso?: string }

type ScreenOrientationComUnlock = ScreenOrientation & { unlock?: () => void }

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [usuario, setUsuario] = useState<UsuarioCTI | null>(null)
  const [loading, setLoading] = useState(true)
  const [erroAcesso, setErroAcesso] = useState(false)
  const [demoraAcesso, setDemoraAcesso] = useState(false)
  const [sessaoOffline, setSessaoOffline] = useState<Session | null>(null)

  useEffect(() => {
    if (!loading) { setDemoraAcesso(false); return }
    const timer = window.setTimeout(() => setDemoraAcesso(true), 15000)
    return () => window.clearTimeout(timer)
  }, [loading, pathname])

  useEffect(() => {
    if (!pathname.startsWith("/crm-app")) return

    const desbloquearOrientacao = () => {
      try {
        const orientacao = window.screen.orientation as ScreenOrientationComUnlock | undefined
        orientacao?.unlock?.()
      } catch (error) {
        console.warn("Não foi possível desbloquear a orientação do dispositivo:", error)
      }
    }

    desbloquearOrientacao()
    window.addEventListener("orientationchange", desbloquearOrientacao)
    window.addEventListener("resize", desbloquearOrientacao)

    if ("serviceWorker" in navigator) {
      void navigator.serviceWorker.getRegistrations().then((registrations) => {
        registrations.forEach((registration) => void registration.update())
      })
    }

    return () => {
      window.removeEventListener("orientationchange", desbloquearOrientacao)
      window.removeEventListener("resize", desbloquearOrientacao)
    }
  }, [pathname])

  useEffect(() => {
    let ativo = true

    async function carregar() {
      setLoading(true)
      setErroAcesso(false)
      setDemoraAcesso(false)
      setUsuario(null)
      setSessaoOffline(null)
      try {
        const supabase = getSupabaseClient()
        const session = await Promise.race([obterSessaoCTI(), new Promise<null>((_, reject) => window.setTimeout(() => reject(new Error("Tempo excedido na validação da sessão.")), 12000))])
        const rotaPublica = ROTAS_PUBLICAS.has(pathname)
        const rotaCrm = pathname.startsWith("/crm-app")
        const rotaPrimeiroAcesso = pathname === "/primeiro-acesso"

        if (!session) {
          if (ativo) setUsuario(null)
          if (!rotaPublica) router.replace(rotaCrm ? "/crm-app/login" : "/login")
          return
        }

        if (pathname === "/redefinir-senha") {
          if (ativo) setUsuario(null)
          return
        }

        if (!navigator.onLine && ["/crm-app", "/crm-app/"].includes(pathname) && session.user?.id && await possuiContextoFeiras(session.user.id)) {
          if (ativo) router.replace("/crm-app/feiras")
          return
        }
        if (!navigator.onLine && pathname === "/crm-app/feiras" && session.expires_at && session.user?.id) {
          if (ativo) setSessaoOffline(session)
          return
        }
        const perfilBase = await Promise.race([buscarUsuarioAtual(), new Promise<null>((_, reject) => window.setTimeout(() => reject(new Error("Tempo excedido na consulta do perfil.")), 12000))])
        if (!ativo) return
        if (sessaoCTIBloqueada()) {
          if (!ROTAS_PUBLICAS.has(pathname)) router.replace(rotaCrm ? "/crm-app/login?acesso=expirado" : "/login?acesso=expirado")
          return
        }
        if (!perfilBase) {
          registrarSessaoCTI(null)
          supabase.auth.stopAutoRefresh()
          if (ativo) setUsuario(null)
          router.replace(rotaCrm ? "/crm-app/login?acesso=negado" : "/login?acesso=negado")
          return
        }

        const perfil = perfilBase as UsuarioComCanais
        const ativoNoSistema = perfil.ativo !== false && !["INATIVO", "BLOQUEADO", "REJEITADO"].includes(String(perfil.status_acesso || ""))
        const primeiroAcessoPendente = perfil.primeiro_acesso_pendente === true || perfil.cadastro_completo === false

        if (ativoNoSistema && primeiroAcessoPendente && !rotaPrimeiroAcesso) {
          if (ativo) setUsuario(perfil)
          router.replace("/primeiro-acesso")
          return
        }

        if (ativoNoSistema && !primeiroAcessoPendente && rotaPrimeiroAcesso) {
          if (ativo) setUsuario(perfil)
          router.replace(rotaInicial(perfil))
          return
        }

        const acessoPermitido = ativoNoSistema && (rotaPrimeiroAcesso || (rotaCrm ? perfil.acesso_crm !== false : perfil.acesso_portal !== false))

        if (!acessoPermitido && !rotaPublica) {
          if (ativo) setUsuario(perfil)
          router.replace(`${rotaCrm ? "/crm-app" : ROTA_PORTAL_PRINCIPAL}?acesso=negado`)
          return
        }

        if (!rotaPublica && !rotaAutorizadaCTI(pathname, perfil)) {
          if (ativo) setUsuario(perfil)
          router.replace(rotaCrm && ["AUTORIZADO_CARRIER","GESTOR_AUTORIZADO_CARRIER"].includes(String(perfil.tipo_usuario).toUpperCase()) ? "/crm-app/feiras?acesso=restrito" : rotaCrm ? "/crm-app?acesso=restrito" : `${ROTA_PORTAL_PRINCIPAL}?acesso=restrito`)
          return
        }

        if (ativo) setUsuario(perfil)
        // Telas públicas de login permanecem acessíveis para recuperação explícita da sessão.
        if (pathname === "/login" && !window.location.search.includes("acesso=")) router.replace(rotaInicial(perfil))
        if (pathname === "/crm-app/login" && !window.location.search.includes("acesso=")) router.replace(perfil.acesso_crm === false && perfil.acesso_portal !== false ? ROTA_PORTAL_PRINCIPAL : "/crm-app")
      } catch (error) {
        console.error("Falha ao resolver identidade CTI:", error)
        if (ativo) { setUsuario(null); setErroAcesso(true) }
        if (!ROTAS_PUBLICAS.has(pathname)) router.replace(pathname.startsWith("/crm-app") ? "/crm-app/login?acesso=indisponivel" : "/login?acesso=indisponivel")
      } finally {
        if (ativo) setLoading(false)
      }
    }

    void carregar()
    return () => { ativo = false }
  }, [pathname, router])

  useEffect(() => {
    const supabase = getSupabaseClient()
    const { data } = supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT") {
        bloquearCofre()
        registrarSessaoCTI(null)
        setUsuario(null)
      }
    })
    const aoSairEmOutraAba = (event: StorageEvent) => {
      if (event.key !== CHAVE_SAIDA_CTI || !event.newValue) return
      bloquearCofre()
      registrarSessaoCTI(null)
      supabase.auth.stopAutoRefresh()
      setUsuario(null)
      router.replace(pathname.startsWith("/crm-app") ? "/crm-app/login" : "/login")
    }
    window.addEventListener("storage", aoSairEmOutraAba)
    return () => { data.subscription.unsubscribe(); window.removeEventListener("storage", aoSairEmOutraAba) }
  }, [pathname, router])

  async function sair() {
    bloquearCofre()
    const supabase = getSupabaseClient()
    const rotaCrm = pathname.startsWith("/crm-app")
    registrarSessaoCTI(null)
    setUsuario(null)
    supabase.auth.stopAutoRefresh()
    router.replace(rotaCrm ? "/crm-app/login" : "/login")
    router.refresh()
  }

  useEffect(() => {
    if (!sessaoOffline) return
    const timer = window.setInterval(() => {
      if (sessaoCTIBloqueada() || !sessaoOffline.expires_at || sessaoOffline.expires_at * 1000 <= Date.now()) {
        bloquearCofre(); setUsuario(null); setSessaoOffline(null); router.replace("/crm-app/login?acesso=expirado")
      }
    }, 1000)
    return () => clearInterval(timer)
  }, [sessaoOffline, router])

  const podeExibir = ROTAS_PUBLICAS.has(pathname) || (!loading && usuario && rotaAutorizadaCTI(pathname, usuario))
  return <AuthContext.Provider value={{ usuario, loading, sair }}>{podeExibir ? children : sessaoOffline && !loading ? <DesbloquearFeirasOffline session={sessaoOffline} aoDesbloquear={setUsuario} /> : <main className="min-h-screen bg-[#020817] p-6 text-slate-300" role="status">{erroAcesso || !loading || demoraAcesso ? <div className="mx-auto max-w-md space-y-4"><p>{loading ? "A validação do acesso está demorando mais que o esperado." : "Não foi possível concluir a validação do acesso ao CTI."} Sua sessão e seus dados não foram apagados.</p><button type="button" onClick={() => window.location.reload()} className="rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950">Tentar novamente</button><a href={pathname.startsWith("/crm-app") ? "/crm-app/login" : "/login"} className="block text-cyan-300 underline">Ir para a tela de login</a></div> : "Validando acesso CTI..."}</main>}</AuthContext.Provider>
}

export function useAuth() { return useContext(AuthContext) }

function DesbloquearFeirasOffline({ session, aoDesbloquear }: { session: Session; aoDesbloquear: (perfil: UsuarioCTI) => void }) {
  const [senha, setSenha] = useState("")
  const [erro, setErro] = useState("")
  const [abrindo, setAbrindo] = useState(false)
  async function abrir(event: React.FormEvent) {
    event.preventDefault(); setErro(""); setAbrindo(true)
    const segredo = senha; setSenha("")
    try {
      const contexto = await recuperarContextoFeiras(session.user.id, segredo)
      if (sessaoCTIBloqueada() || !session.expires_at || session.expires_at * 1000 <= Date.now()) throw Error("Sessão expirada. Conecte-se novamente. As pendências foram preservadas.")
      if (!contexto || !contexto.perfil.ativo || !rotaAutorizadaCTI("/crm-app/feiras", contexto.perfil)) throw Error("Acesso offline não disponível para esta conta.")
      aoDesbloquear(contexto.perfil)
    } catch (error) { bloquearCofre(); setErro(error instanceof Error ? error.message : "Falha ao abrir cofre.") }
    finally { setAbrindo(false) }
  }
  return <main className="min-h-screen bg-[#020817] p-6 text-slate-300"><form onSubmit={e => void abrir(e)} className="mx-auto max-w-md space-y-4 rounded-2xl border border-cyan-800 p-5"><h1 className="text-xl font-bold text-white">Feiras e Eventos · sem conexão</h1><p>Desbloqueie o cofre da conta deste aparelho. O acesso offline dura até a sessão expirar; suas pendências permanecem protegidas.</p><input aria-label="Senha exclusiva do cofre" type="password" required minLength={12} autoComplete="off" value={senha} onChange={e => setSenha(e.target.value)} className="w-full rounded-xl border border-cyan-800 bg-[#07162b] p-3"/><button disabled={abrindo} className="rounded-xl bg-cyan-500 px-4 py-3 text-slate-950">{abrindo ? "Abrindo..." : "Abrir Feiras offline"}</button>{erro && <p role="alert">{erro}</p>}</form></main>
}
