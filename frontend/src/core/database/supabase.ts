import {
  createClient,
  SupabaseClient,
} from "@supabase/supabase-js"

const SUPABASE_CONFIG_ERROR =
  "Supabase frontend não configurado: NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY são obrigatórias."

let supabaseClient: SupabaseClient | null = null

export function getSupabaseClient() {
  if (supabaseClient) {
    return supabaseClient
  }

  const supabaseUrl =
    process.env.NEXT_PUBLIC_SUPABASE_URL

  const supabaseAnonKey =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(SUPABASE_CONFIG_ERROR)
  }

  supabaseClient = createClient(
    supabaseUrl,
    supabaseAnonKey
  )

  return supabaseClient
}
