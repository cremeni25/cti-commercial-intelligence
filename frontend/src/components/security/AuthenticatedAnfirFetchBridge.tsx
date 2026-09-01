"use client"

import { useEffect } from "react"
import { getSupabaseClient } from "@/core/database/supabase"

const ANFIR_WORKBOOK_PATH = "/api/cti/analytics/anfir-workbook-2026"
const CTI_ANALYTICS_PATH = "/api/cti/analytics/"
const CTI_BACKEND_URL = "https://cti-backend-5ugf.onrender.com"

function destinoAnalyticsDireto(url: string) {
  const marcador = "/api/cti/analytics/"
  const indice = url.indexOf(marcador)
  if (indice < 0) return url
  return `${CTI_BACKEND_URL}/analytics/${url.slice(indice + marcador.length)}`
}

export default function AuthenticatedAnfirFetchBridge() {
  useEffect(() => {
    const originalFetch = window.fetch.bind(window)

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url

      if (!url.includes(ANFIR_WORKBOOK_PATH)) {
        if (!url.includes(CTI_ANALYTICS_PATH)) return originalFetch(input, init)
      }

      const metodo = String(init?.method || (input instanceof Request ? input.method : "GET")).toUpperCase()
      const leituraSegura = metodo === "GET" || metodo === "HEAD"
      const supabase = getSupabaseClient()
      const { data, error } = await supabase.auth.getSession()
      let token = data.session?.access_token

      if (error || !token) {
        const renovada = await supabase.auth.refreshSession()
        token = renovada.data.session?.access_token
      }

      if (!token) {
        return new Response(JSON.stringify({ detail: "Sessão CTI não autenticada." }), {
          status: 401,
          headers: { "content-type": "application/json" },
        })
      }

      const headers = new Headers(init?.headers || (input instanceof Request ? input.headers : undefined))
      headers.set("Authorization", `Bearer ${token}`)
      headers.set("Accept", "application/json")

      // Analytics do Dashboard podem processar milhares de evidências ANFIR/CRM.
      // O proxy serverless /api/cti pode encerrar a conexão antes do backend Render
      // terminar o cálculo, apesar de o backend continuar saudável. Para leituras
      // analytics autenticadas, o navegador consulta o backend CTI diretamente.
      const destino = destinoAnalyticsDireto(url)
      const resposta = await originalFetch(destino, { ...init, headers, cache: "no-store" })

      if (resposta.status !== 401 || !leituraSegura) {
        return resposta
      }

      const renovada = await supabase.auth.refreshSession()
      const tokenRenovado = renovada.data.session?.access_token
      if (!tokenRenovado || tokenRenovado === token) {
        return resposta
      }

      const headersRenovados = new Headers(init?.headers || (input instanceof Request ? input.headers : undefined))
      headersRenovados.set("Authorization", `Bearer ${tokenRenovado}`)
      headersRenovados.set("Accept", "application/json")
      return originalFetch(destino, { ...init, headers: headersRenovados, cache: "no-store" })
    }

    return () => {
      window.fetch = originalFetch
    }
  }, [])

  return null
}
