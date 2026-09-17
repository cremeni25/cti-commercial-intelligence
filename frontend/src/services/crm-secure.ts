import { obterTokenCTI } from "@/core/auth/session"
import { API_URL } from "@/lib/api"

const TRANSIENTES = new Set([502, 503, 504])
const TEMPO_LIMITE_GET_MS = 8000
const TEMPO_LIMITE_ESCRITA_MS = 12000

function aguardar(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchComTimeout(url: string, init: RequestInit, timeoutMs: number) {
  if (init.signal) return fetch(url, init)
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("O CTI demorou mais que o esperado para responder. Atualize a tela e tente novamente.")
    }
    throw error
  } finally {
    window.clearTimeout(timer)
  }
}

function erroTransitorio(error: unknown) {
  if (error instanceof TypeError) return true
  if (error instanceof Error && error.message.startsWith("O CTI demorou mais que o esperado")) return true
  return error instanceof DOMException && error.name === "AbortError"
}

async function fetchComRetry(url: string, init: RequestInit, tentativas = 4) {
  const metodo = String(init.method || "GET").toUpperCase()
  const limite = metodo === "GET" ? TEMPO_LIMITE_GET_MS : TEMPO_LIMITE_ESCRITA_MS
  let ultimoErro: unknown = null

  for (let tentativa = 0; tentativa < tentativas; tentativa += 1) {
    try {
      const resposta = await fetchComTimeout(url, init, limite)
      if (metodo !== "GET" || !TRANSIENTES.has(resposta.status) || tentativa === tentativas - 1) return resposta
    } catch (error) {
      ultimoErro = error
      if (metodo !== "GET" || !erroTransitorio(error) || tentativa === tentativas - 1) throw error
    }
    await aguardar(300 * (tentativa + 1))
  }

  throw ultimoErro instanceof Error ? ultimoErro : new Error("O CTI não respondeu dentro do tempo operacional.")
}

export async function buscarNucleoComercialSeguro<T = unknown[]>(): Promise<T> {
  const token = await obterTokenCTI()

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
  const token = await obterTokenCTI()
  const headers = new Headers(init.headers)
  headers.set("Authorization", `Bearer ${token}`)
  return fetchComRetry(`/api/crm-proxy/${path.replace(/^\/+/, "")}`, { ...init, headers })
}
