export const API_URL = "/api/cti"

export async function apiGet(endpoint: string) {
  const response = await fetch(`${API_URL}${endpoint}`, { cache: "no-store" })
  const contentType = response.headers.get("content-type") || ""

  if (!contentType.includes("application/json")) {
    const trecho = (await response.text()).slice(0, 160).replace(/\s+/g, " ")
    throw new Error(`Backend CTI retornou conteúdo inválido (${response.status}): ${trecho || "sem conteúdo"}`)
  }

  const payload = await response.json()

  if (!response.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? String(payload.detail)
      : `Erro do backend CTI: ${response.status}`
    throw new Error(detalhe)
  }

  return payload
}
