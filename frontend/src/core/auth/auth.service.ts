import { getSupabaseClient } from "../database/supabase"
import { UsuarioCTI } from "./types"

function normalizarTipoUsuario(...valores: unknown[]): string {
  const perfis = [
    "ADMIN_MASTER",
    "DIRETOR",
    "GESTOR_REGIONAL",
    "VENDEDOR_REGIONAL",
    "GERENTE",
    "VENDEDOR",
  ]

  for (const valor of valores) {
    const texto = String(valor || "").trim().toUpperCase()
    if (!texto) continue
    const direto = perfis.find((perfil) => texto === perfil || texto.includes(perfil))
    if (direto) return direto
  }

  return ""
}

export async function buscarUsuarioAtual(): Promise<UsuarioCTI | null> {
  const supabase = getSupabaseClient()
  const { data: authData } = await supabase.auth.getUser()
  const authUser = authData.user
  if (!authUser) return null

  let perfil: Record<string, unknown> | null = null

  const porAuthId = await supabase
    .from("cti_users")
    .select("*")
    .eq("auth_id", authUser.id)
    .maybeSingle()

  if (porAuthId.data) {
    perfil = porAuthId.data
  } else if (authUser.email) {
    const porEmail = await supabase
      .from("cti_users")
      .select("*")
      .ilike("email", authUser.email)
      .maybeSingle()
    perfil = porEmail.data
  }

  if (!perfil) return null

  const tipoUsuario = normalizarTipoUsuario(
    perfil.tipo_usuario,
    perfil.perfil,
    perfil.role,
    perfil.cargo,
    authUser.user_metadata?.tipo_usuario,
    authUser.app_metadata?.role,
  )

  return {
    ...perfil,
    id: String(perfil.id || authUser.id),
    auth_id: String(perfil.auth_id || authUser.id),
    nome: String(perfil.nome || authUser.user_metadata?.nome || authUser.email || "Usuário CTI"),
    email: String(perfil.email || authUser.email || ""),
    empresa: String(perfil.empresa || ""),
    cargo: String(perfil.cargo || ""),
    tipo_usuario: tipoUsuario,
    ativo: perfil.ativo !== false,
  } as UsuarioCTI
}
