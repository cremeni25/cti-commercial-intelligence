import type { UsuarioCTI } from "@/core/auth/types"

const PERFIS_ESCOPO_PROPRIO = new Set([
  "REPRES_REGIAO_01",
  "REPRES_REGIAO_02",
  "INDICADOR_VIENA_SP",
])

export function possuiVisaoConsolidada(usuario: UsuarioCTI | null | undefined) {
  const perfil = String(usuario?.tipo_usuario || "").toUpperCase()
  return perfil === "ADMIN_MASTER" || (perfil === "DIRETOR_VIENA_SP" && Boolean(usuario?.acesso_total || usuario?.permissoes?.acesso_total))
}

export function possuiEscopoProprio(usuario: UsuarioCTI | null | undefined) {
  return PERFIS_ESCOPO_PROPRIO.has(String(usuario?.tipo_usuario || "").toUpperCase())
}

export function pertenceAoEscopoDoUsuario(
  responsavelId: string | null | undefined,
  usuario: UsuarioCTI | null | undefined,
) {
  if (!usuario) return false
  if (possuiVisaoConsolidada(usuario)) return true
  if (!possuiEscopoProprio(usuario)) return true
  return Boolean(responsavelId) && String(responsavelId) === String(usuario.id)
}
