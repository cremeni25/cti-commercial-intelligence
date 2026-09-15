import type { Session } from "@supabase/supabase-js"
import { getSupabaseClient } from "../database/supabase"

const SESSION_TIMEOUT_MS = 4000
const MARGEM_EXPIRACAO_MS = 60000
const CHAVE_SESSAO_CTI = "cti-auth-session-v1"

let sessaoCache: Session | null = null
let sessaoEmAndamento: Promise<Session | null> | null = null

function sessaoValida(session: Session | null | undefined) {
  if (!session?.access_token) return false
  if (!session.expires_at) return true
  return session.expires_at * 1000 > Date.now() + MARGEM_EXPIRACAO_MS
}

function lerJsonSessao(bruto: string | null): Session | null {
  if (!bruto) return null
  try {
    const parsed = JSON.parse(bruto) as { currentSession?: Session; session?: Session } & Session
    const candidato = parsed.currentSession || parsed.session || parsed
    return sessaoValida(candidato) ? candidato : null
  } catch {
    return null
  }
}

function lerSessaoCTIPersistida(): Session | null {
  if (typeof window === "undefined") return null

  const propria = lerJsonSessao(window.sessionStorage.getItem(CHAVE_SESSAO_CTI))
  if (propria) return propria

  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    if (!supabaseUrl) return null
    const ref = new URL(supabaseUrl).hostname.split(".")[0]
    const base = `sb-${ref}-auth-token`

    const direta = lerJsonSessao(window.localStorage.getItem(base))
    if (direta) return direta

    const partes: string[] = []
    for (let i = 0; i < 8; i += 1) {
      const parte = window.localStorage.getItem(`${base}.${i}`)
      if (!parte) break
      partes.push(parte)
    }
    if (partes.length) return lerJsonSessao(partes.join(""))
  } catch {
    return null
  }

  return null
}

export function registrarSessaoCTI(session: Session | null) {
  sessaoCache = session
  if (typeof window === "undefined") return
  try {
    if (session && sessaoValida(session)) {
      window.sessionStorage.setItem(CHAVE_SESSAO_CTI, JSON.stringify(session))
    } else {
      window.sessionStorage.removeItem(CHAVE_SESSAO_CTI)
    }
  } catch {
    // cache em memória continua válido mesmo se o storage do navegador estiver indisponível
  }
}

export async function obterSessaoCTI(): Promise<Session | null> {
  if (sessaoValida(sessaoCache)) return sessaoCache

  const persistida = lerSessaoCTIPersistida()
  if (persistida) {
    registrarSessaoCTI(persistida)
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
      registrarSessaoCTI(session)
      return session
    })
    .finally(() => {
      sessaoEmAndamento = null
    })

  return sessaoEmAndamento
}

export async function obterTokenCTI(): Promise<string> {
  if (sessaoValida(sessaoCache)) return sessaoCache!.access_token

  const persistida = lerSessaoCTIPersistida()
  if (persistida?.access_token) {
    registrarSessaoCTI(persistida)
    return persistida.access_token
  }

  const session = await obterSessaoCTI()
  if (!session?.access_token) throw new Error("Sessão CTI não autenticada.")
  return session.access_token
}
