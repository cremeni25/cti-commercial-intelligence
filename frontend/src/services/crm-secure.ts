import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

export async function buscarNucleoComercialSeguro<T = unknown[]>(): Promise<T> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (error || !token) throw new Error("Sessão CTI não autenticada.")

  const response = await fetch(`${API_URL}/crm-seguro/nucleo-comercial`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  })
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = payload && typeof payload === "object" && "detail" in payload
      ? String((payload as { detail?: unknown }).detail || "")
      : ""
    throw new Error(detail || `Falha ao carregar núcleo comercial seguro (${response.status}).`)
  }
  return payload as T
}

export async function fetchCrmSeguroProxy(path: string, init: RequestInit = {}) {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (error || !token) throw new Error("Sessão CTI não autenticada.")
  const headers = new Headers(init.headers)
  headers.set("Authorization", `Bearer ${token}`)
  return fetch(`/api/crm-proxy/${path.replace(/^\/+/, "")}`, { ...init, headers })
}
