export const API_URL = "/api/cti"

export async function apiGet(endpoint: string) {
  const response = await fetch(`${API_URL}${endpoint}`, { cache: "no-store" })
  const contentType = response.headers.get("content-type") || ""

  if (!contentType.includes("application/json")) {
    throw new Error(
      response.status >= 500
        ? "Serviço CTI temporariamente indisponível. Aguarde alguns segundos e tente novamente."
        : `Não foi possível interpretar a resposta do CTI (${response.status}).`,
    )
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
