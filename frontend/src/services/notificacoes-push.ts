import { fetchCrmSeguroProxy } from "@/services/crm-secure"

/** Estados possíveis do resumo diário neste aparelho. */
export type SituacaoPush =
  | "carregando"
  | "sem_suporte"      // navegador sem Web Push (ex.: iPhone fora do app instalado)
  | "servidor_inativo" // chaves ainda não configuradas no backend
  | "bloqueado"        // a pessoa negou a permissão de notificações
  | "inativo"
  | "ativo"

export function suportaPush() {
  return typeof window !== "undefined" && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window
}

export function ehIphoneSemInstalar() {
  if (typeof window === "undefined") return false
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent)
  const instalado = window.matchMedia?.("(display-mode: standalone)").matches || (navigator as Navigator & { standalone?: boolean }).standalone === true
  return ios && !instalado
}

function chaveParaBytes(base64: string) {
  const preenchido = (base64 + "=".repeat((4 - (base64.length % 4)) % 4)).replace(/-/g, "+").replace(/_/g, "/")
  const binario = atob(preenchido)
  return Uint8Array.from(binario, (letra) => letra.charCodeAt(0))
}

async function json<T>(resposta: Response, contexto: string): Promise<T> {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `${contexto} indisponível (${resposta.status}).`)
  }
  return payload as T
}

async function registroDoApp() {
  const existente = await navigator.serviceWorker.getRegistration("/crm-app")
  if (existente) return existente
  // `ready` nunca resolve sem service worker registrado: limite explícito para
  // não deixar o botão preso.
  const pronto = await Promise.race([
    navigator.serviceWorker.ready,
    new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 5000)),
  ])
  if (!pronto) throw new Error("O app ainda está se preparando. Recarregue a página e tente de novo.")
  return pronto
}

export async function lerConfigPush() {
  const resposta = await fetchCrmSeguroProxy("crm-seguro/notificacoes/config", { cache: "no-store" }, { timeoutMs: 15000, tentativas: 2 })
  return json<{ disponivel: boolean; chave_publica: string | null }>(resposta, "A configuração de notificações")
}

export async function situacaoAtualPush(): Promise<SituacaoPush> {
  if (!suportaPush()) return "sem_suporte"
  const config = await lerConfigPush().catch(() => null)
  if (!config?.disponivel || !config.chave_publica) return "servidor_inativo"
  if (Notification.permission === "denied") return "bloqueado"
  const registro = await navigator.serviceWorker.getRegistration("/crm-app")
  const assinatura = await registro?.pushManager.getSubscription()
  return assinatura ? "ativo" : "inativo"
}

export async function ativarResumoDiario() {
  const config = await lerConfigPush()
  if (!config.disponivel || !config.chave_publica) throw new Error("O resumo no celular ainda está sendo ativado no servidor.")
  const permissao = await Notification.requestPermission()
  if (permissao !== "granted") throw new Error("Permita as notificações do CTI nas configurações do aparelho para receber o resumo.")
  const registro = await registroDoApp()
  const assinatura = (await registro.pushManager.getSubscription())
    || (await registro.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: chaveParaBytes(config.chave_publica) }))
  const resposta = await fetchCrmSeguroProxy("crm-seguro/notificacoes/assinatura", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(assinatura.toJSON()),
  })
  await json(resposta, "A inscrição")
}

export async function desativarResumoDiario() {
  const registro = await navigator.serviceWorker.getRegistration("/crm-app")
  const assinatura = await registro?.pushManager.getSubscription()
  if (!assinatura) return
  await fetchCrmSeguroProxy("crm-seguro/notificacoes/assinatura/remover", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint: assinatura.endpoint }),
  }).catch(() => null)
  await assinatura.unsubscribe()
}

export async function enviarNotificacaoTeste() {
  const resposta = await fetchCrmSeguroProxy("crm-seguro/notificacoes/teste", { method: "POST" })
  return json<{ enviadas: number }>(resposta, "O envio de teste")
}
