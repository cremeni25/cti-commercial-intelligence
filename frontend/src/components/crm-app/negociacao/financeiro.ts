export type Registro=Record<string,unknown>
export type Preco={preco_cheio?:number}
export type Equip={codigo:string;linha_produto:string;nome_comercial:string;configuracao?:string;preco_vigente?:Preco|null}
export type Item={id:string;equipamento:string;quantidade:number;preco_tabela:number;preco_unitario:number;desconto_percentual:number;status:string;condicao_pagamento?:string;prazo_entrega?:string;validade_condicao?:string;garantia?:string;opcionais?:string[];observacoes_comerciais?:string;observacoes_tecnicas?:string}
export type FormState={quantidade:string;desconto:string;precoNegociado:string;condicao:string;prazo:string;validade:string;garantia:string;opcionais:string;obsCom:string;obsTec:string}
export const FINAL=new Set(["ACEITO","CONVERTIDO_PEDIDO"])
export const VAZIO:FormState={quantidade:"1",desconto:"0",precoNegociado:"",condicao:"",prazo:"",validade:"",garantia:"",opcionais:"",obsCom:"",obsTec:""}
export function texto(v:unknown){return String(v??"").trim()}
export function num(v:unknown){const n=Number(v||0);return Number.isFinite(n)?n:0}
export function dinheiro(v:unknown){return num(v).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}
export function clamp(v:number,min:number,max:number){return Math.max(min,Math.min(max,v))}
