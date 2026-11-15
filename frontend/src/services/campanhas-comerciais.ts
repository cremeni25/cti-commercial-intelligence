import { fetchCrmSeguroProxy } from "@/services/crm-secure"

export type Rascunho = { mensagem: string; status: "RASCUNHO" | "APROVADA"; aprovada_por: string | null; aprovada_em: string | null; enviados: Record<string, string> }
export type ResumoCampanha = {
  codigo: string
  titulo: string
  publico_descricao: string
  total: number
  com_whatsapp: number
  autorizados: number
  recusaram: number
  rascunho: Rascunho
}
export type PostCanal = { tema: string; texto: string }
export type PainelCampanhas = { campanhas: ResumoCampanha[]; texto_autorizacao: string; posts_canal: PostCanal[] }
export type ClienteCampanha = {
  cliente_id: string
  nome: string | null
  cidade: string | null
  responsavel_nome: string | null
  telefone: string | null
  autorizacao: "AUTORIZADO" | "RECUSADO" | "PENDENTE"
  mensagem: string
  enviado_em: string | null
  link_whatsapp: string | null
}
export type DetalheCampanha = Rascunho & { codigo: string; titulo: string; texto_autorizacao: string; clientes: ClienteCampanha[] }

async function json<T>(resposta: Response, contexto: string): Promise<T> {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `${contexto} indisponível no momento (${resposta.status}).`)
  }
  return payload as T
}

const corpo = (dados: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(dados) })

export async function buscarPainelCampanhas() {
  return json<PainelCampanhas>(await fetchCrmSeguroProxy("crm-seguro/campanhas", { cache: "no-store" }, { timeoutMs: 90000, tentativas: 2 }), "As campanhas")
}

export async function buscarCampanha(codigo: string) {
  return json<DetalheCampanha>(await fetchCrmSeguroProxy(`crm-seguro/campanhas/${encodeURIComponent(codigo)}`, { cache: "no-store" }, { timeoutMs: 90000, tentativas: 2 }), "A campanha")
}

export async function salvarCampanha(codigo: string, mensagem: string, aprovar: boolean) {
  return json<Rascunho>(await fetchCrmSeguroProxy(`crm-seguro/campanhas/${encodeURIComponent(codigo)}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mensagem, aprovar }),
  }, { timeoutMs: 30000, tentativas: 1 }), "A gravação da campanha")
}

export async function marcarEnviado(codigo: string, clienteId: string) {
  return json<{ ok: boolean }>(await fetchCrmSeguroProxy(`crm-seguro/campanhas/${encodeURIComponent(codigo)}/enviado`, corpo({ cliente_id: clienteId }), { timeoutMs: 30000, tentativas: 1 }), "O registro do envio")
}

export async function registrarAutorizacao(clienteId: string, status: "AUTORIZADO" | "RECUSADO") {
  return json<{ status: string }>(await fetchCrmSeguroProxy("crm-seguro/campanhas/autorizacoes", corpo({ cliente_id: clienteId, status, origem: "WhatsApp" }), { timeoutMs: 30000, tentativas: 1 }), "O registro da autorização")
}

export async function baixarCampanhaCsv(codigo: string) {
  const resposta = await fetchCrmSeguroProxy(`crm-seguro/campanhas/${encodeURIComponent(codigo)}/exportacao`, { cache: "no-store" }, { timeoutMs: 90000, tentativas: 1 })
  if (!resposta.ok) throw new Error(`A exportação não está disponível agora (${resposta.status}).`)
  const url = URL.createObjectURL(await resposta.blob())
  const link = document.createElement("a")
  link.href = url
  link.download = `campanha-${codigo.toLowerCase()}.csv`
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}
