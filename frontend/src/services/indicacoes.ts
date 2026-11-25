import { fetchCrmSeguroProxy } from "@/services/crm-secure"

export type Linha = "TRAILER" | "DIESEL TRUCK" | "DIRECT DRIVE"
export type StatusIndicacao = "INDICADA" | "EM_NEGOCIACAO" | "VENDIDA" | "PERDIDA"
export type StatusComissao = "A_PAGAR" | "NF_RECEBIDA" | "PAGA"

export type Indicador = {
  id: string
  nome: string
  documento?: string | null
  telefone?: string | null
  email?: string | null
  regiao?: string | null
  dados_pagamento?: string | null
  ativo?: boolean
}
export type Indicacao = {
  id: string
  indicador_id: string
  indicador_nome: string
  cliente_id: string | null
  cliente_nome: string
  regiao: string | null
  linha: Linha
  modelo: string | null
  quantidade: number
  valor_final: number
  oportunidade_id: string | null
  observacao: string | null
  status: StatusIndicacao
  data_indicacao: string | null
  data_venda: string | null
  comissao_unitaria?: number | null
  comissao_valor?: number | null
  comissao_status?: StatusComissao | null
  nota_fiscal?: string | null
  paga_em?: string | null
}
export type Agregado = {
  indicacoes: number
  em_aberto: number
  vendidas: number
  perdidas: number
  conversao: number | null
  equipamentos_vendidos: number
  valor_vendido: number
  valor_em_aberto: number
  comissao_total: number
  comissao_a_pagar: number
  comissao_nf_recebida: number
  comissao_paga: number
}
export type Painel = {
  periodo: { ano: number | null; mes: number | null }
  tabela_comissao: Record<Linha, number>
  total: Agregado
  peso_nas_vendas: { valor_vendido_viena: number | null; equipamentos_vendidos_viena: number | null; participacao_valor: number | null; participacao_equipamentos: number | null }
  por_indicador: (Agregado & { indicador_id: string; nome: string })[]
  por_regiao: (Agregado & { regiao: string; participacao_no_indicado?: number })[]
  por_linha: (Agregado & { linha: Linha; comissao_por_equipamento: number })[]
}
export type Extrato = { indicador: Indicador; periodo: { ano: number | null; mes: number | null }; resumo: Agregado; indicacoes: Indicacao[] }
export type Acesso = { tabela_comissao: Record<Linha, number> }
export type Periodo = { ano?: number; mes?: number }

async function json<T>(resposta: Response, contexto: string): Promise<T> {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? (payload as { detail?: unknown }).detail : ""
    const texto = Array.isArray(detalhe) ? "Confira os campos preenchidos." : String(detalhe || "")
    throw new Error(texto || `${contexto} indisponível no momento (${resposta.status}).`)
  }
  return payload as T
}

const base = "crm-seguro/indicacoes"
const consulta = (p: Periodo & Record<string, string | number | undefined>) => {
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(p)) if (v !== undefined && v !== "") params.set(k, String(v))
  return params.toString() ? `?${params}` : ""
}
const enviar = (metodo: string, dados: unknown): RequestInit => ({ method: metodo, headers: { "Content-Type": "application/json" }, body: JSON.stringify(dados) })

export async function buscarAcesso() {
  return json<Acesso>(await fetchCrmSeguroProxy(`${base}/acesso`, { cache: "no-store" }, { timeoutMs: 30000, tentativas: 2 }), "O módulo de indicações")
}
export async function buscarIndicadores() {
  return (await json<{ indicadores: Indicador[] }>(await fetchCrmSeguroProxy(`${base}/indicadores`, { cache: "no-store" }, { timeoutMs: 30000, tentativas: 2 }), "Os indicadores")).indicadores
}
export async function salvarIndicador(dados: Omit<Indicador, "id">, id?: string) {
  return json<Indicador>(await fetchCrmSeguroProxy(`${base}/indicadores${id ? `/${encodeURIComponent(id)}` : ""}`, enviar(id ? "PUT" : "POST", dados), { timeoutMs: 30000, tentativas: 1 }), "O cadastro do indicador")
}
export async function buscarIndicacoes(filtros: Periodo & { indicador_id?: string; status?: string } = {}) {
  return (await json<{ indicacoes: Indicacao[] }>(await fetchCrmSeguroProxy(`${base}${consulta(filtros)}`, { cache: "no-store" }, { timeoutMs: 60000, tentativas: 2 }), "As indicações")).indicacoes
}
export async function registrarIndicacao(dados: Record<string, unknown>) {
  return json<Indicacao>(await fetchCrmSeguroProxy(base, enviar("POST", dados), { timeoutMs: 30000, tentativas: 1 }), "O registro da indicação")
}
export async function atualizarIndicacao(id: string, dados: Record<string, unknown>) {
  return json<Indicacao>(await fetchCrmSeguroProxy(`${base}/${encodeURIComponent(id)}`, enviar("PATCH", dados), { timeoutMs: 30000, tentativas: 1 }), "A atualização da indicação")
}
export async function buscarPainel(periodo: Periodo) {
  return json<Painel>(await fetchCrmSeguroProxy(`${base}/painel${consulta(periodo)}`, { cache: "no-store" }, { timeoutMs: 90000, tentativas: 2 }), "O painel de indicadores")
}
export async function buscarExtrato(id: string, periodo: Periodo) {
  return json<Extrato>(await fetchCrmSeguroProxy(`${base}/indicadores/${encodeURIComponent(id)}/extrato${consulta(periodo)}`, { cache: "no-store" }, { timeoutMs: 60000, tentativas: 2 }), "O extrato")
}
export async function baixarExtratoCsv(id: string, periodo: Periodo) {
  const resposta = await fetchCrmSeguroProxy(`${base}/indicadores/${encodeURIComponent(id)}/extrato.csv${consulta(periodo)}`, { cache: "no-store" }, { timeoutMs: 60000, tentativas: 1 })
  if (!resposta.ok) throw new Error(`O extrato não está disponível agora (${resposta.status}).`)
  const url = URL.createObjectURL(await resposta.blob())
  const link = document.createElement("a")
  link.href = url
  link.download = `extrato-indicador${periodo.ano ? `-${periodo.ano}${periodo.mes ? `-${String(periodo.mes).padStart(2, "0")}` : ""}` : ""}.csv`
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}

export const ROTULO_LINHA: Record<Linha, string> = { TRAILER: "Trailer", "DIESEL TRUCK": "Diesel Truck", "DIRECT DRIVE": "Direct Drive" }
export const ROTULO_STATUS: Record<StatusIndicacao, string> = { INDICADA: "Indicada", EM_NEGOCIACAO: "Em negociação", VENDIDA: "Venda concluída", PERDIDA: "Perdida" }
export const ROTULO_COMISSAO: Record<StatusComissao, string> = { A_PAGAR: "Comissão a pagar", NF_RECEBIDA: "NF recebida", PAGA: "Comissão paga" }
