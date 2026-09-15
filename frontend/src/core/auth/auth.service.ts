import { API_URL } from "@/lib/api"
import { obterSessaoCTI } from "./session"
import { UsuarioCTI } from "./types"

const AUTH_TIMEOUT_MS = 8000
const AUTH_TENTATIVAS = 3
const TRANSIENTES = new Set([502, 503, 504])

function aguardar(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function buscarPerfil(token: string) {
  let ultimoErro: unknown = null
  for (let tentativa = 0; tentativa < AUTH_TENTATIVAS; tentativa += 1) {
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), AUTH_TIMEOUT_MS)
    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        method: "GET",
        cache: "no-store",
        signal: controller.signal,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })
      if (!TRANSIENTES.has(response.status) || tentativa === AUTH_TENTATIVAS - 1) return response
    } catch (error) {
      ultimoErro = error
      const transitório = (error instanceof DOMException && error.name === "AbortError") || error instanceof TypeError
      if (!transitório || tentativa === AUTH_TENTATIVAS - 1) throw error
    } finally {
      window.clearTimeout(timer)
    }
    await aguardar(300 * (tentativa + 1))
  }
  throw ultimoErro instanceof Error ? ultimoErro : new Error("Não foi possível validar o perfil CTI.")
}

export async function buscarUsuarioAtual(): Promise<UsuarioCTI | null> {
  const session = await obterSessaoCTI()
  if (!session?.access_token) return null

  const response = await buscarPerfil(session.access_token)

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
