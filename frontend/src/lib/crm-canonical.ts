export const CRM_CANONICAL = {
  clientes: "/api/crm-proxy/crm-seguro/clientes",
  nucleoComercial: "/api/crm-proxy/crm-seguro/nucleo-comercial",
} as const

export const CRM_BACKEND_CANONICAL = {
  clientes: "crm-seguro/clientes",
  nucleoComercial: "crm-seguro/nucleo-comercial",
} as const

export type RegistroCrm = Record<string, unknown>

export function caminhoCanonicoLeitura(caminho: string, metodo: string) {
  if (metodo.toUpperCase() !== "GET") return caminho

  if (caminho === "modulos/clientes" || caminho === "crm-app/clientes") {
    return "crm-seguro/clientes"
  }
  if (caminho === "crm/nucleo-comercial") {
    return "crm-seguro/nucleo-comercial"
  }
  if (caminho === "crm/agenda") {
    return "crm-seguro/agenda"
  }
  if (caminho === "crm/propostas") {
    return "crm-seguro/propostas"
  }
  if (caminho === "crm/pedidos") {
    return "crm-seguro/pedidos"
  }
  if (caminho === "crm/vendas" || caminho === "vendas") {
    return "crm-seguro/vendas"
  }

  if (caminho.startsWith("crm/oportunidades/")) {
    return caminho.replace(/^crm\/oportunidades\//, "crm-seguro/oportunidades/")
  }
  if (caminho.startsWith("crm/propostas/")) {
    return caminho.replace(/^crm\/propostas\//, "crm-seguro/propostas/")
  }
  if (caminho.startsWith("crm/pedidos/")) {
    return caminho.replace(/^crm\/pedidos\//, "crm-seguro/pedidos/")
  }

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