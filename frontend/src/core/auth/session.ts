import type { Session } from "@supabase/supabase-js"
import { getSupabaseClient } from "../database/supabase"

const SESSION_TIMEOUT_MS = 4000
const MARGEM_EXPIRACAO_MS = 5000
const CHAVE_SESSAO_CTI = "cti-auth-session-v1"

let sessaoCache: Session | null = null
let sessaoEmAndamento: Promise<Session | null> | null = null

function sessaoValida(session: Session | null | undefined) {
  if (!session?.access_token) return false
  if (!session.expires_at) return true
  return session.expires_at * 1000 > Date.now() + MARGEM_EXPIRACAO_MS
}

function decodificarBase64Url(valor: string) {
  const normalizado = valor.replace(/-/g, "+").replace(/_/g, "/")
  const padding = normalizado.length % 4 ? "=".repeat(4 - (normalizado.length % 4)) : ""
  return window.atob(normalizado + padding)
}

function normalizarBrutoSessao(bruto: string | null): string | null {
  if (!bruto) return null
  if (!bruto.startsWith("base64-")) return bruto
  try {
    return decodificarBase64Url(bruto.slice(7))
  } catch {
    return null
  }
}

function lerJsonSessao(brutoOriginal: string | null): Session | null {
  const bruto = normalizarBrutoSessao(brutoOriginal)
  if (!bruto) return null
  try {
    const parsed = JSON.parse(bruto) as {
      currentSession?: Session
      session?: Session
      access_token?: string
      expires_at?: number
    } & Session
    const candidato = parsed.currentSession || parsed.session || parsed
    return sessaoValida(candidato) ? candidato : null
  } catch {
    return null
  }
}

function lerStorage(storage: Storage): Session | null {
  const propria = lerJsonSessao(storage.getItem(CHAVE_SESSAO_CTI))
  if (propria) return propria

  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    if (supabaseUrl) {
      const ref = new URL(supabaseUrl).hostname.split(".")[0]
      const base = `sb-${ref}-auth-token`

      const direta = lerJsonSessao(storage.getItem(base))
      if (direta) return direta

      const partes: string[] = []
      for (let i = 0; i < 16; i += 1) {
        const parte = storage.getItem(`${base}.${i}`)
        if (!parte) break
        partes.push(parte)
      }
      if (partes.length) {
        const fragmentada = lerJsonSessao(partes.join(""))
        if (fragmentada) return fragmentada
      }
    }

    for (let i = 0; i < storage.length; i += 1) {
      const chave = storage.key(i)
      if (!chave || !chave.includes("auth-token")) continue

      const direta = lerJsonSessao(storage.getItem(chave))
      if (direta) return direta

      if (chave.endsWith(".0")) {
        const base = chave.slice(0, -2)
        const partes: string[] = []
        for (let parte = 0; parte < 16; parte += 1) {
          const valor = storage.getItem(`${base}.${parte}`)
          if (!valor) break
          partes.push(valor)
        }
        if (partes.length) {
          const fragmentada = lerJsonSessao(partes.join(""))
          if (fragmentada) return fragmentada
        }
      }
    }
  } catch {
    return null
  }

  return null
}

function lerSessaoCTIPersistida(): Session | null {
  if (typeof window === "undefined") return null
  return lerStorage(window.sessionStorage) || lerStorage(window.localStorage)
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
