import { API_URL } from "@/lib/api"
import { getSupabaseClient } from "@/core/database/supabase"
import { UsuarioCTI } from "../types/usuario.types"

export type PerfilCTI = "DIRETOR" | "GESTOR_REGIONAL" | "VENDEDOR_REGIONAL" | "GERENTE" | "VENDEDOR"

export type SolicitacaoAcesso = {
  id: string
  nome: string
  email: string
  telefone?: string | null
  empresa: string
  cargo: string
  canal_solicitado: "PORTAL" | "CRM" | "AMBOS"
  observacoes?: string | null
  status: "PENDENTE" | "CONVITE_ENVIADO" | "APROVADO" | "REJEITADO"
  created_at?: string
}

export type DecisaoSolicitacao = {
  tipo_usuario: PerfilCTI
  territorio?: string
  ddds: string[]
  superior_id?: string
  acesso_portal: boolean
  acesso_crm: boolean
  motivo_decisao?: string
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
  return requisicao<UsuarioCTI[]>("/auth/users")
}

export function listarSolicitacoes(): Promise<SolicitacaoAcesso[]> {
  return requisicao<SolicitacaoAcesso[]>("/auth/access-requests")
}

export function aprovarSolicitacao(id: string, payload: DecisaoSolicitacao) {
  return requisicao(`/auth/access-requests/${id}/approve`, { method: "POST", body: JSON.stringify(payload) })
}

export function rejeitarSolicitacao(id: string, motivo_decisao: string) {
  return requisicao(`/auth/access-requests/${id}/reject`, { method: "POST", body: JSON.stringify({ motivo_decisao }) })
}
