import { API_URL } from "@/lib/api"
import { getSupabaseClient } from "../database/supabase"
import { UsuarioCTI } from "./types"

export async function buscarUsuarioAtual(): Promise<UsuarioCTI | null> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  const session = data.session

  if (error || !session?.access_token) return null

  const response = await fetch(`${API_URL}/auth/me`, {
    method: "GET",
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = payload?.detail || `Falha ao resolver o perfil CTI (${response.status}).`
    throw new Error(detail)
  }

  const perfil = await response.json()

  return {
    id: String(perfil.id || session.user.id),
    auth_id: String(perfil.auth_id || session.user.id),
    nome: String(perfil.nome || session.user.email || "Usuário CTI"),
    email: String(perfil.email || session.user.email || ""),
    empresa: String(perfil.empresa || ""),
    cargo: String(perfil.cargo || ""),
    tipo_usuario: String(perfil.tipo_usuario || "").trim().toUpperCase(),
    ativo: perfil.ativo !== false,
    acesso_portal: perfil.acesso_portal !== false,
    acesso_crm: perfil.acesso_crm !== false,
    status_acesso: String(perfil.status_acesso || ""),
    primeiro_acesso_pendente: perfil.primeiro_acesso_pendente === true,
    cadastro_completo: perfil.cadastro_completo !== false,
    territorio: perfil.territorio ? String(perfil.territorio) : null,
    ddds: Array.isArray(perfil.ddds) ? perfil.ddds.map((item: unknown) => String(item)) : [],
    permissoes: perfil.permissoes && typeof perfil.permissoes === "object" ? perfil.permissoes : {},
    acesso_total: Boolean(perfil.acesso_total),
  }
}
