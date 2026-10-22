"use client"

// Only ciphertext and KDF metadata persist. Unlock keys never leave this module.
const DB = "cti-feiras-cofre-v1"
const STORE = "registros"
const META = "cofres"
const ITERATIONS = 600000
const TTL = 5 * 60 * 1000
export type RegistroCifrado = { id: string; userId: string; salt: number[]; iv: number[]; ciphertext: number[]; criadoEm: string }
export type AtendimentoLocal = { id: string; feiraId: string; atendimentoId?: string; payload: Record<string, unknown> }
type Cofre = { userId: string; salt: number[]; iv: number[]; ciphertext: number[]; iterations: number }
type Aberto = { chave: CryptoKey; salt: number[]; expira: number }
const chaves = new Map<string, Aberto>()
let geracaoCofre = 0
const encoder = new TextEncoder()
function abrir(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open(DB, 3)
    r.onupgradeneeded = () => {
      if (!r.result.objectStoreNames.contains(STORE)) r.result.createObjectStore(STORE, { keyPath: "id" })
      if (!r.result.objectStoreNames.contains("contextos")) r.result.createObjectStore("contextos", { keyPath: "authId" })
      if (!r.result.objectStoreNames.contains(META)) r.result.createObjectStore(META, { keyPath: "userId" })
    }
    r.onsuccess = () => resolve(r.result)
    r.onerror = () => reject(r.error)
    r.onblocked = () => reject(Error("Feche outras abas do CTI para atualizar o cofre."))
  })
}
async function operar<T>(nome: string, modo: IDBTransactionMode, fn: (s: IDBObjectStore, done: (v: T) => void) => void): Promise<T> {
  const db = await abrir()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(nome, modo)
    let valor: T
    tx.oncomplete = () => { db.close(); resolve(valor) }
    tx.onabort = tx.onerror = () => { db.close(); reject(tx.error || Error("Transação local interrompida.")) }
    try { fn(tx.objectStore(nome), v => { valor = v }) } catch (e) { tx.abort(); reject(e) }
  })
}
const chaveRegistro = (userId: string, id: string) => JSON.stringify([userId, id])
async function metadados(userId: string): Promise<Cofre | undefined> {
  return operar(META, "readonly", (s, done) => { const r = s.get(userId); r.onsuccess = () => done(r.result) })
}
async function listarCifrados(userId: string): Promise<RegistroCifrado[]> {
  return operar(STORE, "readonly", (s, done) => { const r = s.getAll(); r.onsuccess = () => done((r.result as RegistroCifrado[]).filter(x => x.userId === userId)) })
}
async function derivar(senha: string, salt: number[], iterations: number): Promise<CryptoKey> {
  if (senha.length < 12) throw Error("Use uma senha exclusiva do cofre com pelo menos 12 caracteres.")
  const base = await crypto.subtle.importKey("raw", encoder.encode(senha), "PBKDF2", false, ["deriveKey"])
  return crypto.subtle.deriveKey({ name: "PBKDF2", salt: new Uint8Array(salt), iterations, hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"])
}
function aad(userId: string, id: string) { return encoder.encode(userId + ":" + id) }
async function decifrar(reg: RegistroCifrado, chave: CryptoKey): Promise<AtendimentoLocal> {
  const raw = await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(reg.iv), additionalData: aad(reg.userId, reg.id) }, chave, new Uint8Array(reg.ciphertext))
  const item = JSON.parse(new TextDecoder().decode(raw)) as AtendimentoLocal
  // v1 used the UUID alone as the storage key; v2 namespaces it by user.
  if (reg.id !== item.id && reg.id !== chaveRegistro(reg.userId, item.id)) throw Error("Identidade local inconsistente.")
  return item
}
export async function desbloquearCofre(userId: string, senha: string): Promise<void> {
  bloquearCofre()
  const geracaoInicial = geracaoCofre
  const meta = await metadados(userId)
  const antigos = meta ? [] : await listarCifrados(userId)
  const salt = meta?.salt || antigos[0]?.salt || Array.from(crypto.getRandomValues(new Uint8Array(16)))
  const iterations = meta?.iterations || (antigos.length ? 310000 : ITERATIONS)
  const chave = await derivar(senha, salt, iterations)
  try {
    if (meta) await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(meta.iv), additionalData: aad(userId, "verificador") }, chave, new Uint8Array(meta.ciphertext))
    // Validate all legacy ciphertext before persisting the password verifier.
    for (const item of antigos) await decifrar(item, chave)
  } catch { throw Error("Senha incorreta ou dados locais corrompidos. As pendências foram preservadas.") }
  if (geracaoInicial !== geracaoCofre) throw Error("Desbloqueio cancelado. A sessão ou o estado do cofre mudou.")
  if (!meta) {
    const iv = crypto.getRandomValues(new Uint8Array(12))
    const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: aad(userId, "verificador") }, chave, encoder.encode("CTI offline vault v2"))
    // add(), rather than put(), prevents two tabs establishing different passwords.
    await operar<void>(META, "readwrite", (s, done) => { s.add({ userId, salt, iterations, iv: Array.from(iv), ciphertext: Array.from(new Uint8Array(ciphertext)) }); done(undefined) })
  }
  if (geracaoInicial !== geracaoCofre) throw Error("Desbloqueio cancelado. O cofre permanece bloqueado.")
  chaves.set(userId, { chave, salt, expira: Date.now() + TTL })
}
export function bloquearCofre(userId?: string) {
  geracaoCofre += 1
  if (userId) chaves.delete(userId); else chaves.clear()
  if (typeof window !== "undefined") window.dispatchEvent(new Event("cti-cofre-bloqueado"))
}
export function cofreDesbloqueado(userId: string) {
  const aberto = chaves.get(userId)
  if (aberto && aberto.expira <= Date.now()) { bloquearCofre(userId); return false }
  return Boolean(aberto)
}
function exigir(userId: string) {
  if (!cofreDesbloqueado(userId)) throw Error("Desbloqueie o cofre antes de continuar.")
  return chaves.get(userId)!
}
export async function salvarCifrado(userId: string, atendimento: AtendimentoLocal) {
  const { chave, salt } = exigir(userId)
  const id = chaveRegistro(userId, atendimento.id)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: aad(userId, id) }, chave, encoder.encode(JSON.stringify(atendimento)))
  exigir(userId) // a logout during encryption must not reopen a key or acknowledge a save
  await operar<void>(STORE, "readwrite", (s, done) => { s.add({ id, userId, salt, iv: Array.from(iv), ciphertext: Array.from(new Uint8Array(ciphertext)), criadoEm: new Date().toISOString() }); done(undefined) })
}
export async function listarDecifrados(userId: string): Promise<AtendimentoLocal[]> {
  const { chave } = exigir(userId)
  const result = await Promise.all((await listarCifrados(userId)).map(r => decifrar(r, chave)))
  exigir(userId)
  return result
}
export async function confirmarSincronizacao(userId: string, id: string) {
  exigir(userId)
  await operar<void>(STORE, "readwrite", (s, done) => {
    const key = chaveRegistro(userId, id)
    s.delete(key)
    const legacy = s.get(id)
    legacy.onsuccess = () => { if (legacy.result?.userId === userId) s.delete(id) }
    done(undefined)
  })
}
export async function quantidadePendente(userId: string) { return (await listarCifrados(userId)).length }
export async function sincronizarCofre(userId: string, enviar: (item: AtendimentoLocal) => Promise<{ id: string }>) {
  const executar = async () => {
    let enviados = 0
    for (const item of await listarDecifrados(userId)) {
      exigir(userId)
      const resposta = await enviar(item)
      if (!resposta?.id) throw Error("Confirmação inválida. Pendência preservada.")
      await confirmarSincronizacao(userId, item.id)
      enviados++
    }
    return enviados
  }
  if (typeof navigator !== "undefined" && navigator.locks) return navigator.locks.request("cti-feiras-sync:" + userId, executar)
  return executar() // concurrent retries are also serialized by the server idempotency key
}

export type ContextoFeirasOffline = {
  perfil: import("@/core/auth/types").UsuarioCTI
  feiras: { id: string; nome: string; inicio: string; fim: string }[]
  catalogo: { codigo: string; linha_produto: string; nome_comercial: string }[]
  expiraEm: number
}
type ContextoCifrado = { authId: string; userId: string; iv: number[]; ciphertext: number[] }
export async function salvarContextoFeiras(contexto: ContextoFeirasOffline) {
  const { perfil } = contexto
  if (!perfil.auth_id || contexto.expiraEm <= Date.now()) throw Error("Sessão expirada. Conecte-se novamente para preparar o uso offline.")
  const { chave } = exigir(perfil.id)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: aad(perfil.id, "contexto:" + perfil.auth_id) }, chave, encoder.encode(JSON.stringify(contexto)))
  exigir(perfil.id)
  await operar<void>("contextos", "readwrite", (s, done) => { s.put({ authId: perfil.auth_id, userId: perfil.id, iv: Array.from(iv), ciphertext: Array.from(new Uint8Array(ciphertext)) }); done(undefined) })
}
export async function lerContextoFeiras(authId: string): Promise<ContextoFeirasOffline | null> {
  const reg = await operar<ContextoCifrado | undefined>("contextos", "readonly", (s, done) => { const r = s.get(authId); r.onsuccess = () => done(r.result) })
  if (!reg) return null
  const { chave } = exigir(reg.userId)
  const raw = await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(reg.iv), additionalData: aad(reg.userId, "contexto:" + authId) }, chave, new Uint8Array(reg.ciphertext))
  exigir(reg.userId)
  const contexto = JSON.parse(new TextDecoder().decode(raw)) as ContextoFeirasOffline
  if (contexto.perfil.auth_id !== authId || contexto.perfil.id !== reg.userId || contexto.expiraEm <= Date.now()) throw Error("Contexto offline expirado ou inconsistente. Conecte-se novamente. As pendências foram preservadas.")
  return contexto
}
export async function recuperarContextoFeiras(authId: string, senha: string) {
  const reg = await operar<ContextoCifrado | undefined>("contextos", "readonly", (s, done) => { const r = s.get(authId); r.onsuccess = () => done(r.result) })
  if (!reg) throw Error("Este dispositivo ainda não foi preparado para uso offline com esta conta. Conecte-se para carregar Feiras.")
  try {
    await desbloquearCofre(reg.userId, senha)
    return await lerContextoFeiras(authId)
  } catch (error) { bloquearCofre(); throw error }
}

/** Indica somente se esta conta preparou Feiras; não libera nem revela seu perfil. */
export async function possuiContextoFeiras(authId: string): Promise<boolean> {
  return operar<boolean>("contextos", "readonly", (s, done) => { const r = s.getKey(authId); r.onsuccess = () => done(r.result !== undefined) })
}
