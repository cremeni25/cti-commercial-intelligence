import { ROLES } from "./roles"

export const ACCESS = {
  ADMIN_MASTER: [
    "*",
  ],

  CEO: [
    "dashboard",
    "clientes",
    "oportunidades",
    "pipeline",
    "performance",
    "territorios",
  ],

  DIRETOR_ADMINISTRATIVO: [
    "dashboard",
    "clientes",
    "oportunidades",
    "pipeline",
    "performance",
    "territorios",
  ],

  GERENTE_LATAM: [
    "dashboard",
    "clientes",
    "oportunidades",
    "pipeline",
    "performance",
  ],

  GERENTE_NACIONAL: [
    "dashboard",
    "clientes",
    "oportunidades",
    "pipeline",
    "performance",
  ],

  GESTOR_REGIONAL: [
    "dashboard",
    "clientes",
    "oportunidades",
    "pipeline",
  ],

  VENDEDOR: [
    "dashboard",
    "clientes",
    "oportunidades",
  ],
} as const

export function hasAccess(
  role: keyof typeof ACCESS,
  permission: string
) {
  const permissions =
    ACCESS[role] as readonly string[]

  if (!permissions) {
    return false
  }

  if (permissions.includes("*")) {
    return true
  }

  return permissions.includes(permission)
}