import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

const TRANSIENTES = new Set([502, 503, 504])

function aguardar(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchComRetry(url: string, init: RequestInit, tentativas = 3) {
  let resposta = await fetch(url, init)
  const metodo = String(init.method || "GET").toUpperCase()
  if (metodo !== "GET") return resposta
  for (let tentativa = 1; tentativa < tentativas && TRANSIENTES.has(resposta.status); tentativa += 1) {
    await aguardar(350 * tentativa)
    resposta = await fetch(url, init)
  }
  return resposta
}

export async function buscarNucleoComercialSeguro<T = unknown[]>(): Promise<T> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (error || !token) throw new Error("Sessão CTI não autenticada.")

  const response = await fetchComRetry(`${API_URL}/crm-seguro/nucleo-comercial`, {
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
  return fetchComRetry(`/api/crm-proxy/${path.replace(/^\/+/, "")}`, { ...init, headers })
}
