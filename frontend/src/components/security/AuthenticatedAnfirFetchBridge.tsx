"use client"

import { useEffect } from "react"
import { getSupabaseClient } from "@/core/database/supabase"

const ANFIR_WORKBOOK_PATH = "/api/cti/analytics/anfir-workbook-2026"

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
        return originalFetch(input, init)
      }

      const supabase = getSupabaseClient()
      const { data, error } = await supabase.auth.getSession()
      const token = data.session?.access_token
      if (error || !token) {
        return new Response(JSON.stringify({ detail: "Sessão CTI não autenticada." }), {
          status: 401,
          headers: { "content-type": "application/json" },
        })
      }

      const headers = new Headers(init?.headers)
      headers.set("Authorization", `Bearer ${token}`)
      return originalFetch(input, { ...init, headers })
    }

    return () => {
      window.fetch = originalFetch
    }
  }, [])

  return null
}
