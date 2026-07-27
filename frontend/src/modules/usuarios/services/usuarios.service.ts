import { API_URL } from "@/lib/api"
import { getSupabaseClient } from "@/core/database/supabase"
import { UsuarioCTI } from "../types/usuario.types"

export type NovoUsuarioCTI = {
  nome: string
  email: string
  senha: string
  empresa: string
  cargo: string
  tipo_usuario: "DIRETOR" | "GESTOR_REGIONAL" | "VENDEDOR_REGIONAL" | "GERENTE" | "VENDEDOR"
  territorio?: string
  ddds: string[]
  superior_id?: string
}

async function tokenAtual() {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  if (error || !data.session?.access_token) throw new Error("Sessão autenticada não encontrada.")
  return data.session.access_token
}

export async function listarUsuarios(): Promise<UsuarioCTI[]> {
  const token = await tokenAtual()
  const response = await fetch(`${API_URL}/auth/users`, {
    method: "GET",
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail || `Falha ao carregar usuários (${response.status}).`)
  }
  return response.json()
}

export async function criarUsuario(payload: NovoUsuarioCTI): Promise<UsuarioCTI> {
  const token = await tokenAtual()
  const response = await fetch(`${API_URL}/auth/users`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail || `Falha ao criar usuário (${response.status}).`)
  }
  return response.json()
}
