"use client"

import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react"

import {
  UsuarioCTI,
} from "./types"

import {
  buscarUsuarioAtual,
} from "./auth.service"

interface AuthContextType {
  usuario: UsuarioCTI | null
  loading: boolean
}

const AuthContext =
  createContext<AuthContextType>({
    usuario: null,
    loading: true,
  })

export function AuthProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const [usuario, setUsuario] =
    useState<UsuarioCTI | null>(null)

  const [loading, setLoading] =
    useState(true)

  useEffect(() => {
    let ativo = true

    async function carregar() {
      try {
        const data = await buscarUsuarioAtual()
        if (ativo) setUsuario(data)
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
  }, [])

  return (
    <AuthContext.Provider
      value={{
        usuario,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
