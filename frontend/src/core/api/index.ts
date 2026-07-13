const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000"

async function request(
  endpoint: string,
  options: RequestInit = {}
) {
  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    }
  )

  if (!response.ok) {
    throw new Error(
      `Erro ${response.status}`
    )
  }

  return response.json()
}

export function apiGet(endpoint: string) {
  return request(endpoint)
}

export function apiPost(
  endpoint: string,
  body: unknown
) {
  return request(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export function apiPut(
  endpoint: string,
  body: unknown
) {
  return request(endpoint, {
    method: "PUT",
    body: JSON.stringify(body),
  })
}

export function apiDelete(endpoint: string) {
  return request(endpoint, {
    method: "DELETE",
  })
}

export { API_URL }