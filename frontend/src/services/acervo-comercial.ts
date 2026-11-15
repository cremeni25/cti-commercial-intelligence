import { fetchCrmSeguroProxy } from "@/services/crm-secure"

export type PessoaCarteira = {
  usuario_id: string
  nome: string | null
  email: string | null
  tipo_usuario: string | null
  ativo: boolean
  clientes: number
  negocios_abertos: number
  atividades_pendentes: number
}
export type ResumoCarteiras = { pessoas: PessoaCarteira[]; clientes_sem_responsavel: number; carteiras_paradas: number }
export type BackupAcervo = { arquivo: string; criado_em: string; motivo: string; bytes: number; totais: Record<string, number>; url?: string | null }
export type ResultadoTransferencia = { clientes: number; negocios_abertos: number; atividades_pendentes: number; historico_preservado: number; backup?: string }

async function json<T>(resposta: Response, contexto: string): Promise<T> {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `${contexto} indisponível no momento (${resposta.status}).`)
  }
  return payload as T
}

export async function buscarCarteiras() {
  return json<ResumoCarteiras>(await fetchCrmSeguroProxy("crm-seguro/acervo/carteiras", { cache: "no-store" }, { timeoutMs: 60000, tentativas: 2 }), "As carteiras")
}

export async function buscarBackups() {
  const dados = await json<{ backups: BackupAcervo[] }>(await fetchCrmSeguroProxy("crm-seguro/acervo/backups", { cache: "no-store" }, { timeoutMs: 30000, tentativas: 2 }), "As cópias")
  return dados.backups || []
}

export async function gerarBackup() {
  return json<BackupAcervo>(await fetchCrmSeguroProxy("crm-seguro/acervo/backups", { method: "POST" }, { timeoutMs: 240000, tentativas: 1 }), "A cópia do acervo")
}

export async function transferirCarteira(de: string, para: string, motivo: string) {
  return json<ResultadoTransferencia>(await fetchCrmSeguroProxy("crm-seguro/acervo/transferir", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ de_usuario_id: de, para_usuario_id: para, motivo }),
  }, { timeoutMs: 240000, tentativas: 1 }), "A transferência")
}
