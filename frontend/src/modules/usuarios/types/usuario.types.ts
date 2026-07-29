export interface UsuarioCTI {
  id: string
  auth_id: string
  nome: string
  email: string
  empresa: string
  cargo: string
  tipo_usuario: string
  ativo: boolean
  territorio?: string | null
  ddds?: string[]
  superior_id?: string | null
  acesso_portal?: boolean
  acesso_crm?: boolean
  status_acesso?: string
  created_at: string
}
