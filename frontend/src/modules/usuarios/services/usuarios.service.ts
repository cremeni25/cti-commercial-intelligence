import { getSupabaseClient } from "@/core/database/supabase"
import { UsuarioCTI } from "../types/usuario.types"

export async function listarUsuarios(): Promise<UsuarioCTI[]> {
  const supabase = getSupabaseClient()

  const { data, error } = await supabase
    .from("cti_users")
    .select("*")
    .order("created_at", {
      ascending: false,
    })

  if (error) {
    console.error(error)
    return []
  }

  return data as UsuarioCTI[]
}
