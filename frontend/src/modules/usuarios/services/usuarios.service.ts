import { API_URL } from "@/lib/api"
import { getSupabaseClient } from "@/core/database/supabase"
import { UsuarioCTI } from "../types/usuario.types"

export async function listarUsuarios(): Promise<UsuarioCTI[]> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()

  if (error || !data.session?.access_token) {
    throw new Error("Sessão autenticada não encontrada.")
  }

  const response = await fetch(`${API_URL}/auth/users`, {
    method: "GET",
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${data.session.access_token}`,
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail || `Falha ao carregar usuários (${response.status}).`)
  }

  return response.json()
}
