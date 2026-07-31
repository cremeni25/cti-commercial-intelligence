import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

export type ModeloHomologacao = {
  id: string
  linha_produto: string
  equipamento: string
  versao: number
  arquivo_template_nome_original: string
  arquivo_template_tamanho_bytes: number
  arquivo_template_hash_sha256: string
  url_temporaria: string
  url_valida_por_segundos: number
  situacao: string
}

async function authHeaders() {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  if (error || !data.session?.access_token) throw new Error("Sessão autenticada não encontrada.")
  return { Authorization: `Bearer ${data.session.access_token}` }
}

async function detailMessage(response: Response) {
  const payload = await response.json().catch(() => null)
  const detail = payload?.detail
  if (typeof detail === "string") return detail
  if (detail && typeof detail === "object") return JSON.stringify(detail)
  return `Falha na homologação (${response.status}).`
}

export async function carregarFilaHomologacao(): Promise<{ total_pendente: number; fila: ModeloHomologacao[] }> {
  const response = await fetch(`${API_URL}/modelos-proposta-homologacao/fila`, {
    cache: "no-store",
    headers: await authHeaders(),
  })
  if (!response.ok) throw new Error(await detailMessage(response))
  return response.json()
}

export async function homologarModelos(itens: ModeloHomologacao[]) {
  const response = await fetch(`${API_URL}/modelos-proposta-homologacao/homologar-lote`, {
    method: "POST",
    headers: { ...(await authHeaders()), "Content-Type": "application/json" },
    body: JSON.stringify({
      itens: itens.map((item) => ({
        modelo_id: item.id,
        sha256_confirmado: item.arquivo_template_hash_sha256,
        validacao_visual_integral: true,
      })),
    }),
  })
  if (!response.ok) throw new Error(await detailMessage(response))
  return response.json()
}
