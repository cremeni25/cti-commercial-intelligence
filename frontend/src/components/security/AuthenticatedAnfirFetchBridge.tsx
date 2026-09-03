"use client"

import { useEffect } from "react"
import { getSupabaseClient } from "@/core/database/supabase"

const ANFIR_WORKBOOK_PATH = "/api/cti/analytics/anfir-workbook-2026"
const CTI_ANALYTICS_PATH = "/api/cti/analytics/"
const CRM_PROXY_PATH = "/api/crm-proxy/"

export default function AuthenticatedAnfirFetchBridge() {
  useEffect(() => {
    const originalFetch = window.fetch.bind(window)

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url

      const leituraCti = url.includes(ANFIR_WORKBOOK_PATH) || url.includes(CTI_ANALYTICS_PATH) || url.includes(CRM_PROXY_PATH)
      if (!leituraCti) return originalFetch(input, init)

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
      const resposta = await originalFetch(input, { ...init, headers })

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
      return originalFetch(input, { ...init, headers: headersRenovados })
    }

    return () => {
      window.fetch = originalFetch
    }
  }, [])

  return null
}