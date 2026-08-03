import { API_URL } from "@/lib/api"
import { getSupabaseClient } from "@/core/database/supabase"
import { UsuarioCTI } from "../types/usuario.types"

export type PermissoesUsuario = {
  acesso_portal: boolean
  acesso_crm: boolean
  dashboard_executivo: boolean
  clientes_visualizar: boolean
  clientes_editar: boolean
  oportunidades_visualizar: boolean
  oportunidades_editar: boolean
  propostas_visualizar: boolean
  propostas_emitir: boolean
  pedidos_visualizar: boolean
  pedidos_converter: boolean
  pedidos_enviar: boolean
  financeiro_visualizar: boolean
  usuarios_administrar: boolean
  configuracoes_administrar: boolean
  acesso_total: boolean
}

export type UsuarioNovo = {
  nome: string
  email: string
  senha_temporaria: string
  empresa: string
  funcao: string
  territorio?: string
  ddds: string[]
  gestor_responsavel?: string | null
  permissoes: PermissoesUsuario
}

async function tokenAtual() {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  if (error || !data.session?.access_token) throw new Error("Sessão autenticada não encontrada.")
  return data.session.access_token
}

async function requisicao<T>(url: string, init?: RequestInit): Promise<T> {
  const token = await tokenAtual()
  const response = await fetch(`${API_URL}${url}`, {
    ...init,
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...(init?.headers || {}) },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail || `Falha na operação (${response.status}).`)
  }
  return response.json()
}

export function listarUsuarios(): Promise<UsuarioCTI[]> {
  return requisicao<UsuarioCTI[]>("/governanca/usuarios")
}

export function criarUsuario(payload: UsuarioNovo): Promise<UsuarioCTI> {
  return requisicao<UsuarioCTI>("/governanca/usuarios", { method: "POST", body: JSON.stringify(payload) })
}

export function atualizarPermissoes(usuarioId: string, permissoes: PermissoesUsuario) {
  return requisicao<PermissoesUsuario>(`/governanca/usuarios/${usuarioId}/permissoes`, {
    method: "PUT",
    body: JSON.stringify(permissoes),
  })
}
