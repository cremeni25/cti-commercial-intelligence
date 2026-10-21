"use client"

// Fila local por usuário; não armazena credenciais. Limpar ao encerrar sessão em dispositivos compartilhados.
export type FeiraPendente = { id: string; userId: string; feiraId: string; payload: Record<string, unknown>; criadoEm: string }
const DB = "cti-feiras-pendentes-v1"
const STORE = "atendimentos"

function abrir(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1)
    req.onupgradeneeded = () => { if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE, { keyPath: "id" }) }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}
async function executar<T>(modo: IDBTransactionMode, fn: (store: IDBObjectStore, done: (value: T) => void) => void): Promise<T> {
  const db = await abrir()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, modo)
    let result: T
    tx.oncomplete = () => { db.close(); resolve(result) }
    tx.onerror = () => { db.close(); reject(tx.error) }
    fn(tx.objectStore(STORE), v => { result = v })
  })
}
export function enfileirarFeira(item: FeiraPendente) {
  return executar<void>("readwrite", (store, done) => { store.put(item); done(undefined) })
}
export function listarPendentesFeira(userId: string): Promise<FeiraPendente[]> {
  return executar("readonly", (store, done) => {
    const req = store.getAll()
    req.onsuccess = () => done((req.result as FeiraPendente[]).filter(x => x.userId === userId).sort((a,b) => a.criadoEm.localeCompare(b.criadoEm)))
  })
}
export function removerPendenteFeira(id: string) {
  return executar<void>("readwrite", (store, done) => { store.delete(id); done(undefined) })
}
export async function sincronizarFeiras(userId: string, enviar: (item: FeiraPendente) => Promise<boolean>) {
  let enviados = 0
  for (const item of await listarPendentesFeira(userId)) {
    if (!(await enviar(item))) break
    await removerPendenteFeira(item.id)
    enviados++
  }
  return enviados
}
