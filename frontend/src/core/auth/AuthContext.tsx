"use client"

import { createContext, useContext, useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { getSupabaseClient } from "../database/supabase"
import { UsuarioCTI } from "./types"
import { buscarUsuarioAtual } from "./auth.service"

interface AuthContextType {
  usuario: UsuarioCTI | null
  loading: boolean
  sair: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  usuario: null,
  loading: true,
  sair: async () => undefined,
})

const ROTAS_PUBLICAS = new Set(["/login", "/redefinir-senha"])

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [usuario, setUsuario] = useState<UsuarioCTI | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let ativo = true

    async function carregar() {
      try {
        const supabase = getSupabaseClient()
        const { data } = await supabase.auth.getSession()
        const rotaPublica = ROTAS_PUBLICAS.has(pathname)

        if (!data.session) {
          if (ativo) setUsuario(null)
          if (!rotaPublica) router.replace("/login")
          return
        }

        // O Supabase cria uma sessão temporária durante PASSWORD_RECOVERY.
        // Essa rota deve permanecer aberta até a nova senha ser salva.
        if (pathname === "/redefinir-senha") {
          if (ativo) setUsuario(null)
          return
        }

        const perfil = await buscarUsuarioAtual()
        if (ativo) setUsuario(perfil)
        if (pathname === "/login" && perfil) router.replace("/dashboard")
      } catch (error) {
        console.error("Falha ao resolver identidade CTI:", error)
        if (ativo) setUsuario(null)
      } finally {
        if (ativo) setLoading(false)
      }
    }

    void carregar()

    return () => {
      ativo = false
    }
  }, [pathname, router])

  async function sair() {
    const supabase = getSupabaseClient()
    await supabase.auth.signOut()
    setUsuario(null)
    router.replace("/login")
    router.refresh()
  }

  return (
    <AuthContext.Provider value={{ usuario, loading, sair }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
