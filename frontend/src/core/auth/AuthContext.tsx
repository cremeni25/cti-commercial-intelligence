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

        if (!data.session) {
          if (ativo) setUsuario(null)
          if (pathname !== "/login") router.replace("/login")
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
