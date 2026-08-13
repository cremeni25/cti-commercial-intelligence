"use client"

import { Pencil } from "lucide-react"
import { FINAL, type Item, dinheiro } from "./financeiro"

export default function ItemFinanceiroCard({item,indice,onEdit}:{item:Item;indice:number;onEdit:(item:Item)=>void}){
 const unit=item.preco_tabela*(1-item.desconto_percentual/100)
 const desconto=item.preco_tabela-unit
 const subtotal=unit*item.quantidade
 const final=FINAL.has(item.status.toUpperCase())
 return <article className="rounded-2xl border border-[#24466f] bg-[#091a33] p-4"><div className="flex items-start justify-between gap-3"><div><span className="text-[10px] uppercase tracking-[.16em] text-cyan-400">Item {indice+1}</span><strong className="mt-1 block">{item.equipamento}</strong></div><button type="button" disabled={final} onClick={()=>onEdit(item)} className="flex items-center gap-1 rounded-lg border border-[#24466f] px-2 py-1 text-xs text-slate-300 disabled:opacity-40"><Pencil size={13}/>{final?"Finalizado":"Editar"}</button></div><div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3"><Info l="Tabela unitária" v={dinheiro(item.preco_tabela)}/><Info l="Desconto" v={`${item.desconto_percentual.toLocaleString("pt-BR",{maximumFractionDigits:2})}% · ${dinheiro(desconto)}`}/><Info l="Unitário negociado" v={dinheiro(unit)} hi/><Info l="Quantidade" v={`${item.quantidade} un.`}/><Info l="Subtotal" v={dinheiro(subtotal)} hi/><Info l="Status" v={item.status}/></div></article>
}

export function Info({l,v,hi=false}:{l:string;v:string;hi?:boolean}){return <div className="rounded-xl border border-[#24466f] bg-[#020817] p-3"><span className="block text-[10px] uppercase tracking-[.1em] text-slate-500">{l}</span><strong className={`mt-1 block text-sm ${hi?"text-emerald-300":"text-slate-200"}`}>{v||"—"}</strong></div>}
