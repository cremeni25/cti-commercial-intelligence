export interface PermissoesSessaoCTI {
  acesso_portal?: boolean
  acesso_crm?: boolean
  dashboard_executivo?: boolean
  clientes_visualizar?: boolean
  clientes_editar?: boolean
  oportunidades_visualizar?: boolean
  oportunidades_editar?: boolean
  propostas_visualizar?: boolean
  propostas_emitir?: boolean
  pedidos_visualizar?: boolean
  pedidos_converter?: boolean
  pedidos_enviar?: boolean
  financeiro_visualizar?: boolean
  usuarios_administrar?: boolean
  configuracoes_administrar?: boolean
  acesso_total?: boolean
  [chave: string]: boolean | undefined
}

export interface UsuarioCTI {
  id: string
  auth_id: string
  nome: string
  email: string
  empresa: string
  cargo: string
  tipo_usuario: string
  ativo: boolean
  acesso_portal?: boolean
  acesso_crm?: boolean
  status_acesso?: string
  territorio?: string | null
  ddds?: string[]
  permissoes?: PermissoesSessaoCTI
  acesso_total?: boolean
}
