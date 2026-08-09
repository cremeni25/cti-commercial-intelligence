const API_URL = "/api/cti"

export type OperationalContextValue = "brasil" | "viena-sp" | `uf-${string}` | `ddd-${string}`

async function request(endpoint: string) {
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
      : `Erro ao carregar ${endpoint}`
    throw new Error(detalhe)
  }
  return payload
}

export async function getDashboardExecutivo() { return request("/analytics/dashboard") }
export async function getDashboardExecutivoContextual(query: string | OperationalContextValue) {
  const qs = query.includes("=") ? query : `contexto=${encodeURIComponent(query)}`
  return request(`/analytics/dashboard?${qs}`)
}
export async function getImplementadorasContextuais(query: string | OperationalContextValue) {
  const qs = query.includes("=") ? query : `contexto=${encodeURIComponent(query)}`
  return request(`/modulos/implementadoras?${qs}`)
}
export async function getBrasilDashboard() { return request("/brasil/dashboard") }
export async function getBrasilImplementadoras() { return request("/brasil/implementadoras") }
export async function getVienaDashboard() { return request("/autorizados/viena-sp/dashboard") }
export async function getVienaImplementadoras() { return request("/autorizados/viena-sp/implementadoras") }
export async function getVienaHistorico() { return request("/autorizados/viena-sp/historico") }
export async function getInsights() { return request("/dashboard/insights") }
export async function getPipelineStatus() { return request("/pipeline/status") }

export async function uploadArquivo(file: File, contexto: OperationalContextValue = "brasil") {
  const formData = new FormData(); formData.append("file", file); formData.append("contexto_operacional", contexto)
  const response = await fetch(`${API_URL}/upload/anfir/seguro`, { method: "POST", body: formData })
  if (!response.ok) throw new Error("Erro ao realizar upload")
  return response.json()
}

export async function processarPipeline() { return request("/pipeline/status") }
export async function getDebugAmostra() { return request("/debug/amostra") }
