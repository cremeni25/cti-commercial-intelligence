import type { Session } from "@supabase/supabase-js"
import { getSupabaseClient } from "../database/supabase"

const SESSION_TIMEOUT_MS = 4000
const MARGEM_EXPIRACAO_MS = 60000

let sessaoCache: Session | null = null
let sessaoEmAndamento: Promise<Session | null> | null = null

function sessaoValida(session: Session | null | undefined) {
  if (!session?.access_token) return false
  if (!session.expires_at) return true
  return session.expires_at * 1000 > Date.now() + MARGEM_EXPIRACAO_MS
}

function lerSessaoPersistida(): Session | null {
  if (typeof window === "undefined") return null
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    if (!supabaseUrl) return null
    const ref = new URL(supabaseUrl).hostname.split(".")[0]
    const bruto = window.localStorage.getItem(`sb-${ref}-auth-token`)
    if (!bruto) return null
    const parsed = JSON.parse(bruto) as { currentSession?: Session; session?: Session } & Session
    const candidato = parsed.currentSession || parsed.session || parsed
    return sessaoValida(candidato) ? candidato : null
  } catch {
    return null
  }
}

export function registrarSessaoCTI(session: Session | null) {
  sessaoCache = session
}

export async function obterSessaoCTI(): Promise<Session | null> {
  if (sessaoValida(sessaoCache)) return sessaoCache

  const persistida = lerSessaoPersistida()
  if (persistida) {
    sessaoCache = persistida
    return persistida
  }

  if (sessaoEmAndamento) return sessaoEmAndamento

  const supabase = getSupabaseClient()
  sessaoEmAndamento = Promise.race([
    supabase.auth.getSession().then(({ data, error }) => {
      if (error) throw error
      return data.session
    }),
    new Promise<never>((_, reject) => {
      window.setTimeout(() => reject(new Error("A sessão CTI não respondeu dentro do tempo operacional.")), SESSION_TIMEOUT_MS)
    }),
  ])
    .then((session) => {
      if (session) sessaoCache = session
      return session
    })
    .finally(() => {
      sessaoEmAndamento = null
    })

  return sessaoEmAndamento
}

export async function obterTokenCTI(): Promise<string> {
  const session = await obterSessaoCTI()
  if (!session?.access_token) throw new Error("Sessão CTI não autenticada.")
  return session.access_token
}
