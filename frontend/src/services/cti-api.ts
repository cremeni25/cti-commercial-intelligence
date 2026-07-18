const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://cti-backend-5ugf.onrender.com"

export type OperationalContextValue = "brasil" | "viena-sp"

async function request(endpoint: string) {
  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      cache: "no-store",
    }
  )

  if (!response.ok) {
    throw new Error(
      `Erro ao carregar ${endpoint}`
    )
  }

  return response.json()
}

function contextoQuery(contexto: OperationalContextValue) {
  return `?contexto=${encodeURIComponent(contexto)}`
}

export async function getDashboardExecutivo() {
  return request("/analytics/dashboard")
}

export async function getDashboardExecutivoContextual(contexto: OperationalContextValue) {
  return request(`/analytics/dashboard${contextoQuery(contexto)}`)
}

export async function getImplementadorasContextuais(contexto: OperationalContextValue) {
  if (contexto === "viena-sp") {
    return getVienaImplementadoras()
  }
  return getBrasilImplementadoras()
}

export async function getBrasilDashboard() {
  return request("/brasil/dashboard")
}

export async function getBrasilImplementadoras() {
  return request("/brasil/implementadoras")
}

export async function getVienaDashboard() {
  return request("/autorizados/viena-sp/dashboard")
}

export async function getVienaImplementadoras() {
  return request("/autorizados/viena-sp/implementadoras")
}

export async function getVienaHistorico() {
  return request("/autorizados/viena-sp/historico")
}

export async function getInsights() {
  return request("/dashboard/insights")
}

export async function getPipelineStatus() {
  return request("/pipeline/status")
}

export async function uploadArquivo(
  file: File,
  contexto: OperationalContextValue = "brasil"
) {
  const formData = new FormData()

  formData.append("file", file)
  formData.append("contexto_operacional", contexto)

  const response = await fetch(
    `${API_URL}/upload/anfir/seguro`,
    {
      method: "POST",
      body: formData,
    }
  )

  if (!response.ok) {
    throw new Error(
      "Erro ao realizar upload"
    )
  }

  return response.json()
}

export async function processarPipeline() {
  return request("/pipeline/status")
}

export async function getDebugAmostra() {
  return request("/debug/amostra")
}
