const API_URL =
  process.env.NEXT_PUBLIC_API_URL

export async function getDashboardExecutivo() {
  const response = await fetch(
    `${API_URL}/analytics/dashboard`,
    {
      cache: "no-store",
    }
  )

  if (!response.ok) {
    throw new Error(
      "Erro ao carregar dashboard"
    )
  }

  return response.json()
}

export async function getInsights() {
  const response = await fetch(
    `${API_URL}/dashboard/insights`,
    {
      cache: "no-store",
    }
  )

  if (!response.ok) {
    throw new Error(
      "Erro ao carregar insights"
    )
  }

  return response.json()
}

export async function getPipelineStatus() {
  const response = await fetch(
    `${API_URL}/pipeline/status`,
    {
      cache: "no-store",
    }
  )

  if (!response.ok) {
    throw new Error(
      "Erro ao carregar pipeline"
    )
  }

  return response.json()
}

export async function uploadArquivo(
  file: File
) {
  const formData = new FormData()

  formData.append("file", file)

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
  return {
    status: "PIPELINE_INTEGRADO",
  }
}

export async function getDebugAmostra() {
  const response = await fetch(
    `${API_URL}/debug/amostra`,
    {
      cache: "no-store",
    }
  )

  if (!response.ok) {
    throw new Error(
      "Erro ao carregar auditoria"
    )
  }

  return response.json()
}