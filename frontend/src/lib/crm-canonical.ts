export const CRM_CANONICAL = {
  clientes: "/api/crm-proxy/crm-app/clientes",
  nucleoComercial: "/api/crm-proxy/crm/nucleo-comercial",
} as const

export const CRM_BACKEND_CANONICAL = {
  clientes: "crm-app/clientes",
  nucleoComercial: "crm/nucleo-comercial",
} as const

export type RegistroCrm = Record<string, unknown>

export function caminhoCanonicoLeitura(caminho: string, metodo: string) {
  if (metodo.toUpperCase() !== "GET") return caminho
  if (caminho === "modulos/clientes") return CRM_BACKEND_CANONICAL.clientes
  return caminho
}

export function listaCrm(payload: unknown): RegistroCrm[] {
  if (Array.isArray(payload)) return payload as RegistroCrm[]
  if (payload && typeof payload === "object") {
    const objeto = payload as RegistroCrm
    for (const chave of ["dados", "itens", "resultado", "atividades", "oportunidades"]) {
      if (Array.isArray(objeto[chave])) return objeto[chave] as RegistroCrm[]
    }
  }
  return []
}
