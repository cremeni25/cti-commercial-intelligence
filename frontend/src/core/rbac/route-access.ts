import type { PermissoesSessaoCTI, UsuarioCTI } from "@/core/auth/types"

function tem(permissoes: PermissoesSessaoCTI | undefined, chave: keyof PermissoesSessaoCTI) {
  return permissoes?.[chave] === true
}

function inicia(pathname: string, prefixo: string) {
  return pathname === prefixo || pathname.startsWith(`${prefixo}/`)
}

export function rotaAutorizadaCTI(pathname: string, usuario: UsuarioCTI) {
  const perfil = String(usuario.tipo_usuario || "").toUpperCase()
  const permissoes = usuario.permissoes
  const master = perfil === "ADMIN_MASTER"
  const diretorIntegral = perfil === "DIRETOR_VIENA_SP" && Boolean(usuario.acesso_total || permissoes?.acesso_total)
  const gestao = master || diretorIntegral

  if (["/", "/login", "/redefinir-senha", "/crm-app/login", "/solicitar-acesso"].includes(pathname)) return true

  // Ferramentas técnicas e de homologação não pertencem à operação diretiva.
  if (inicia(pathname, "/backoffice-fontes")) return master
  if (inicia(pathname, "/configuracoes/modelos-oficiais")) return master
  if (inicia(pathname, "/crm-app/testes-arquivados")) return master
  if (inicia(pathname, "/crm-app/controle-financeiro")) return master

  if (inicia(pathname, "/usuarios")) return master || tem(permissoes, "usuarios_administrar")
  if (inicia(pathname, "/configuracoes")) return master || tem(permissoes, "configuracoes_administrar")
  if (inicia(pathname, "/upload")) return gestao

  if (inicia(pathname, "/dashboard")) return gestao || tem(permissoes, "dashboard_executivo")
  if (inicia(pathname, "/empresas") || inicia(pathname, "/implementadoras")) return gestao || tem(permissoes, "clientes_visualizar")
  if (inicia(pathname, "/oportunidades") || inicia(pathname, "/pipeline") || inicia(pathname, "/historico-comercial") || inicia(pathname, "/ia-comercial") || inicia(pathname, "/atividades") || inicia(pathname, "/forecast") || inicia(pathname, "/mapa-estrategico") || inicia(pathname, "/detalhamento") || inicia(pathname, "/equipamentos")) return gestao || tem(permissoes, "oportunidades_visualizar")
  if (inicia(pathname, "/propostas")) return gestao || tem(permissoes, "propostas_visualizar")
  if (inicia(pathname, "/pedidos")) return gestao || tem(permissoes, "pedidos_visualizar")
  if (inicia(pathname, "/vendas") || inicia(pathname, "/relatorios") || inicia(pathname, "/funil-carrier")) return gestao || tem(permissoes, "dashboard_executivo")

  if (inicia(pathname, "/crm-app/clientes")) return gestao || tem(permissoes, "clientes_visualizar") || tem(permissoes, "clientes_editar")
  if (inicia(pathname, "/crm-app/oportunidades") || inicia(pathname, "/crm-app/pipeline") || inicia(pathname, "/crm-app/forecast") || inicia(pathname, "/crm-app/agenda") || inicia(pathname, "/crm-app/atividades") || inicia(pathname, "/crm-app/visitas") || inicia(pathname, "/crm-app/historico")) return gestao || tem(permissoes, "oportunidades_visualizar") || tem(permissoes, "oportunidades_editar")
  if (inicia(pathname, "/crm-app/propostas")) return gestao || tem(permissoes, "propostas_visualizar") || tem(permissoes, "propostas_emitir")
  if (inicia(pathname, "/crm-app/pedidos")) return gestao || tem(permissoes, "pedidos_visualizar") || tem(permissoes, "pedidos_converter") || tem(permissoes, "pedidos_enviar")
  if (inicia(pathname, "/crm-app/vendas")) return gestao || tem(permissoes, "dashboard_executivo")
  if (pathname === "/crm-app") return usuario.acesso_crm !== false

  // Rotas novas não são abertas implicitamente para perfis operacionais.
  return master
}
