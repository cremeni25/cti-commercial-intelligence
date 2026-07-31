import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

export type ImportacaoPacoteResultado = {
  ok: boolean
  total_esperado: number
  importados: number
  ignorados_ja_armazenados: number
  resultados: Array<{
    modelo_id: string
    equipamento: string
    arquivo: string
    caminho?: string
    status: string
  }>
}

export async function importarPacoteModelos(file: File): Promise<ImportacaoPacoteResultado> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()

  if (error || !data.session?.access_token) {
    throw new Error("Sessão autenticada não encontrada.")
  }

  const formData = new FormData()
  formData.append("arquivo", file)

  const response = await fetch(`${API_URL}/modelos-proposta-importacao/pacote`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${data.session.access_token}`,
    },
    body: formData,
  })

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || `Falha ao importar o pacote (${response.status}).`)
  }

  return payload as ImportacaoPacoteResultado
}
