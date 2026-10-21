"use client"

// Cofre offline: chave somente em memória; senha não é gravada. O PIN deve ser exclusivo deste cofre.
const DB = "cti-feiras-cofre-v1"
const STORE = "registros"
const ITERATIONS = 310000
export type RegistroCifrado = { id: string; userId: string; salt: number[]; iv: number[]; ciphertext: number[]; criadoEm: string }
export type AtendimentoLocal = { id: string; feiraId: string; payload: Record<string, unknown> }
const chaves = new Map<string, CryptoKey>()
function bytes(a: number[]) { return new Uint8Array(a) }
function abrir(): Promise<IDBDatabase> { return new Promise((resolve,reject)=>{ const r=indexedDB.open(DB,1);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE,{keyPath:"id"})};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error) }) }
function operar<T>(modo: IDBTransactionMode, executar: (s: IDBObjectStore, done: (v:T)=>void)=>void): Promise<T> {return abrir().then(db=>new Promise<T>((resolve,reject)=>{const tx=db.transaction(STORE,modo);let valor:T;tx.oncomplete=()=>{db.close();resolve(valor)};tx.onerror=()=>{db.close();reject(tx.error)};executar(tx.objectStore(STORE),v=>{valor=v})}))}
async function derivar(senha:string,salt:Uint8Array):Promise<CryptoKey>{if(senha.length<12)throw Error("Use uma senha do cofre com pelo menos 12 caracteres.");const base=await crypto.subtle.importKey("raw",new TextEncoder().encode(senha),"PBKDF2",false,["deriveKey"]);return crypto.subtle.deriveKey({name:"PBKDF2",salt:Uint8Array.from(salt),iterations:ITERATIONS,hash:"SHA-256"},base,{name:"AES-GCM",length:256},false,["encrypt","decrypt"])}
export async function desbloquearCofre(userId:string,senha:string):Promise<void>{const salt=await obterSal(userId);const chave=await derivar(senha,salt);const existentes=await listarCifrados(userId);if(existentes.length){try{await decifrar(existentes[0],chave)}catch{throw Error("Senha incorreta ou dados locais corrompidos.")}}chaves.set(userId,chave)}
async function obterSal(userId:string):Promise<Uint8Array>{const existentes=await listarCifrados(userId);if(existentes.length)return bytes(existentes[0].salt);const novo=crypto.getRandomValues(new Uint8Array(16));sais.set(userId,novo);return novo}
const sais=new Map<string,Uint8Array>()
export function bloquearCofre(userId?:string){if(userId){chaves.delete(userId);sais.delete(userId)}else{chaves.clear();sais.clear()}}
export function cofreDesbloqueado(userId:string){return chaves.has(userId)}
async function listarCifrados(userId:string):Promise<RegistroCifrado[]>{return operar("readonly",(store,done)=>{const r=store.getAll();r.onsuccess=()=>done((r.result as RegistroCifrado[]).filter(x=>x.userId===userId))})}
async function decifrar(reg:RegistroCifrado,chave:CryptoKey):Promise<AtendimentoLocal>{const raw=await crypto.subtle.decrypt({name:"AES-GCM",iv:bytes(reg.iv),additionalData:new TextEncoder().encode(reg.userId+":"+reg.id)},chave,bytes(reg.ciphertext));return JSON.parse(new TextDecoder().decode(raw)) as AtendimentoLocal}
export async function salvarCifrado(userId:string,atendimento:AtendimentoLocal){const chave=chaves.get(userId);if(!chave)throw Error("Desbloqueie o cofre antes de salvar.");const salt=await obterSal(userId);const iv=crypto.getRandomValues(new Uint8Array(12));const raw=new TextEncoder().encode(JSON.stringify(atendimento));const ciphertext=await crypto.subtle.encrypt({name:"AES-GCM",iv,additionalData:new TextEncoder().encode(userId+":"+atendimento.id)},chave,raw);const registro:RegistroCifrado={id:atendimento.id,userId,salt:Array.from(salt),iv:Array.from(iv),ciphertext:Array.from(new Uint8Array(ciphertext)),criadoEm:new Date().toISOString()};await operar<void>("readwrite",(store,done)=>{store.put(registro);done(undefined)})}
export async function listarDecifrados(userId:string):Promise<AtendimentoLocal[]>{const chave=chaves.get(userId);if(!chave)throw Error("Cofre bloqueado.");return Promise.all((await listarCifrados(userId)).map(r=>decifrar(r,chave)))}
export function confirmarSincronizacao(id:string){return operar<void>("readwrite",(store,done)=>{store.delete(id);done(undefined)})}
export async function quantidadePendente(userId:string){return (await listarCifrados(userId)).length}
