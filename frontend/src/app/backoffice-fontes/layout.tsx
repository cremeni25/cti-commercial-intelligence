"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

import { useAuth } from "@/core/auth/AuthContext"

export default function BackofficeFontesLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { usuario, loading } = useAuth()
  const adminMaster = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"

  useEffect(() => {
    if (!loading && usuario && !adminMaster) router.replace("/dashboard")
  }, [adminMaster, loading, router, usuario])

  if (loading || !usuario) {
    return <main className="min-h-screen bg-[#020817]" aria-busy="true" />
  }

  if (!adminMaster) {
    return <main className="min-h-screen bg-[#020817]" aria-busy="true" />
  }

  return children
}
