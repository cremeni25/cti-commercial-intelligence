export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://cti-backend-5ugf.onrender.com"

export async function apiGet(
  endpoint: string
) {
  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      cache: "no-store",
    }
  )

  if (!response.ok) {
    throw new Error(
      `Erro API: ${response.status}`
    )
  }

  return response.json()
}