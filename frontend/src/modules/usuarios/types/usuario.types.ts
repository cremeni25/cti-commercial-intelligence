import type { PermissoesUsuario } from "../services/usuarios.service"

export interface UsuarioCTI {
  id: string
  auth_id: string
  nome: string
  email: string
  empresa: string
  cargo: string
  funcao?: string | null
  tipo_usuario: string
  ativo: boolean
  territorio?: string | null
  ddds?: string[]
  gestor_responsavel?: string | null
  acesso_portal?: boolean
  acesso_crm?: boolean
  status_acesso?: string
  primeiro_acesso_pendente?: boolean
  cadastro_completo?: boolean
  permissoes?: Partial<PermissoesUsuario>
  created_at: string
}
