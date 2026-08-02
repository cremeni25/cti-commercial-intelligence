const BACKEND_PADRAO = "https://cti-backend-5ugf.onrender.com"

function resolverApiUrl() {
  const configurada = String(process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "")

  if (!configurada) return BACKEND_PADRAO

  try {
    const host = new URL(configurada).hostname.toLowerCase()
    const apontaParaFrontend =
      host === "app.cti-intelligence.com" ||
      host.endsWith(".vercel.app") ||
      host.includes("cti-commercial-intelligence")

    return apontaParaFrontend ? BACKEND_PADRAO : configurada
  } catch {
    return BACKEND_PADRAO
  }
}

export const API_URL = resolverApiUrl()

export async function apiGet(endpoint: string) {
  const response = await fetch(`${API_URL}${endpoint}`, { cache: "no-store" })
  const contentType = response.headers.get("content-type") || ""

  if (!contentType.includes("application/json")) {
    const trecho = (await response.text()).slice(0, 120).replace(/\s+/g, " ")
    throw new Error(`API retornou conteúdo inválido (${response.status}): ${trecho || "sem conteúdo"}`)
  }

  const payload = await response.json()

  if (!response.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? String(payload.detail)
      : `Erro API: ${response.status}`
    throw new Error(detalhe)
  }

  return payload
}
