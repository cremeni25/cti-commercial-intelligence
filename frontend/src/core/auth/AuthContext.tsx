"use client"

import { createContext, useContext, useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { getSupabaseClient } from "../database/supabase"
import { UsuarioCTI } from "./types"
import { buscarUsuarioAtual } from "./auth.service"
import { rotaAutorizadaCTI } from "@/core/rbac/route-access"

interface AuthContextType {
  usuario: UsuarioCTI | null
  loading: boolean
  sair: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({ usuario: null, loading: true, sair: async () => undefined })
const ROTAS_PUBLICAS = new Set(["/", "/login", "/redefinir-senha", "/crm-app/login", "/solicitar-acesso"])

type UsuarioComCanais = UsuarioCTI & { acesso_portal?: boolean; acesso_crm?: boolean; status_acesso?: string }

type ScreenOrientationComUnlock = ScreenOrientation & { unlock?: () => void }

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [usuario, setUsuario] = useState<UsuarioCTI | null>(null)
  const [loading, setLoading] = useState(true)

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
      try {
        const supabase = getSupabaseClient()
        const { data } = await supabase.auth.getSession()
        const rotaPublica = ROTAS_PUBLICAS.has(pathname)
        const rotaCrm = pathname.startsWith("/crm-app")

        if (!data.session) {
          if (ativo) setUsuario(null)
          if (!rotaPublica) router.replace(rotaCrm ? "/crm-app/login" : "/login")
          return
        }

        if (pathname === "/redefinir-senha") {
          if (ativo) setUsuario(null)
          return
        }

        const perfilBase = await buscarUsuarioAtual()
        if (!perfilBase) {
          await supabase.auth.signOut()
          if (ativo) setUsuario(null)
          router.replace(rotaCrm ? "/crm-app/login?acesso=negado" : "/login?acesso=negado")
          return
        }

        const perfil = perfilBase as UsuarioComCanais
        const ativoNoSistema = perfil.ativo !== false && !["INATIVO", "BLOQUEADO", "REJEITADO"].includes(String(perfil.status_acesso || ""))
        const acessoPermitido = ativoNoSistema && (rotaCrm ? perfil.acesso_crm !== false : perfil.acesso_portal !== false)

        if (!acessoPermitido && !rotaPublica) {
          if (ativo) setUsuario(perfil)
          router.replace(`${rotaCrm ? "/crm-app" : "/dashboard"}?acesso=negado`)
          return
        }

        if (!rotaPublica && !rotaAutorizadaCTI(pathname, perfil)) {
          if (ativo) setUsuario(perfil)
          router.replace(rotaCrm ? "/crm-app?acesso=restrito" : "/dashboard?acesso=restrito")
          return
        }

        if (ativo) setUsuario(perfil)
        if (pathname === "/login") router.replace(perfil.acesso_portal === false && perfil.acesso_crm !== false ? "/crm-app" : "/dashboard")
        if (pathname === "/crm-app/login") router.replace(perfil.acesso_crm === false && perfil.acesso_portal !== false ? "/dashboard" : "/crm-app")
      } catch (error) {
        console.error("Falha ao resolver identidade CTI:", error)
        if (ativo) setUsuario(null)
      } finally {
        if (ativo) setLoading(false)
      }
    }

    void carregar()
    return () => { ativo = false }
  }, [pathname, router])

  async function sair() {
    const supabase = getSupabaseClient()
    const rotaCrm = pathname.startsWith("/crm-app")
    await supabase.auth.signOut()
    setUsuario(null)
    router.replace(rotaCrm ? "/crm-app/login" : "/login")
    router.refresh()
  }

  return <AuthContext.Provider value={{ usuario, loading, sair }}>{children}</AuthContext.Provider>
}

export function useAuth() { return useContext(AuthContext) }
