import { getSupabaseClient } from "../database/supabase"
import { UsuarioCTI } from "./types"

function normalizarTipoUsuario(valor: unknown, cargo: unknown): string {
  const direto = String(valor || "").trim().toUpperCase()
  if (direto) return direto

  const textoCargo = String(cargo || "").trim().toUpperCase()
  const perfis = [
    "ADMIN_MASTER",
    "DIRETOR",
    "GESTOR_REGIONAL",
    "VENDEDOR_REGIONAL",
    "GERENTE",
    "VENDEDOR",
  ]

  return perfis.find((perfil) => textoCargo.includes(perfil)) || ""
}

export async function buscarUsuarioAtual(): Promise<UsuarioCTI | null> {
  const supabase = getSupabaseClient()

  const { data: authData } = await supabase.auth.getUser()
  if (!authData.user) return null

  const { data, error } = await supabase
    .from("cti_users")
    .select("*")
    .eq("auth_id", authData.user.id)
    .single()

  if (error || !data) return null

  return {
    ...data,
    auth_id: String(data.auth_id || authData.user.id),
    nome: String(data.nome || authData.user.user_metadata?.nome || authData.user.email || "Usuário CTI"),
    email: String(data.email || authData.user.email || ""),
    empresa: String(data.empresa || ""),
    cargo: String(data.cargo || ""),
    tipo_usuario: normalizarTipoUsuario(data.tipo_usuario, data.cargo),
    ativo: data.ativo !== false,
  } as UsuarioCTI
}
