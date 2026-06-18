import { supabase } from "../database/supabase"
import { UsuarioCTI } from "./types"

export async function buscarUsuarioAtual():
Promise<UsuarioCTI | null> {

  const {
    data: authData,
  } = await supabase.auth.getUser()

  if (!authData.user) {
    return null
  }

  const { data } =
    await supabase
      .from("cti_users")
      .select("*")
      .eq("auth_id", authData.user.id)
      .single()

  return data
}