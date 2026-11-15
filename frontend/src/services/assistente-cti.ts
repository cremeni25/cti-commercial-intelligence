import { fetchCrmSeguroProxy } from "@/services/crm-secure"

export type AcaoAssistente = { href: string; titulo: string }
export type RespostaAssistente = {
  pergunta: string
  resposta: string
  destaques: { cliente_id: string; nome: string | null; cidade: string | null; frota: number }[]
  acoes: AcaoAssistente[]
}
export type ResultadoBusca = {
  telas: AcaoAssistente[]
  empresas: { cliente_id: string; nome: string | null; cidade: string | null; grupo: string; href: string }[]
  equipamentos: { modelo: string; linha: string | null; href: string }[]
}

async function json<T>(resposta: Response, contexto: string): Promise<T> {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `${contexto} indisponível no momento (${resposta.status}).`)
  }
  return payload as T
}

export async function perguntarAoCTI(pergunta: string) {
  return json<RespostaAssistente>(await fetchCrmSeguroProxy("crm-seguro/assistente/perguntar", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pergunta }),
  }, { timeoutMs: 90000, tentativas: 1 }), "O assistente")
}

export async function buscarNoCTI(termo: string, sinal?: AbortSignal) {
  return json<ResultadoBusca>(await fetchCrmSeguroProxy(`crm-seguro/assistente/buscar?q=${encodeURIComponent(termo)}`, { cache: "no-store", signal: sinal }, { timeoutMs: 30000, tentativas: 1 }), "A busca")
}
