import type { UsuarioCTI } from "@/core/auth/types"

export function possuiVisaoConsolidada(usuario: UsuarioCTI | null | undefined) {
  const perfil = String(usuario?.tipo_usuario || "").toUpperCase()
  return perfil === "ADMIN_MASTER" || (perfil === "DIRETOR_VIENA_SP" && Boolean(usuario?.acesso_total || usuario?.permissoes?.acesso_total))
}

export function pertenceAoEscopoDoUsuario(
  responsavelId: string | null | undefined,
  usuario: UsuarioCTI | null | undefined,
) {
  if (!usuario) return false
  if (possuiVisaoConsolidada(usuario)) return true
  return Boolean(responsavelId) && String(responsavelId) === String(usuario.id)
}
