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
    async function carregar() {
      const data =
        await buscarUsuarioAtual()

      setUsuario(data)
      setLoading(false)
    }

    carregar()
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