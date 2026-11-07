"use client"

import Link from "next/link"
import { useMemo, useState } from "react"
import { Check, Copy, FileText, Snowflake } from "lucide-react"
import type { TabelaAplicacao } from "@/services/inteligencia-comercial"

const TEMPERATURAS = [0, -10, -18, -20, -22, -25] as const

function grau(valor: number) {
  return `${valor > 0 ? "+" : ""}${valor} °C`
}

/**
 * "Qual equipamento atende?" — escolha o tamanho do baú e a temperatura que o
 * cliente precisa; a tabela oficial diz quais equipamentos chegam lá.
 */
export default function TabelaAplicacaoView({ tabela, onCopiado, documentoHref }: { tabela: TabelaAplicacao; onCopiado: (mensagem: string) => void; documentoHref: string }) {
  const [tamanho, setTamanho] = useState(3)
  const [alvo, setAlvo] = useState<number>(-18)
  const [copiado, setCopiado] = useState(false)

  const atendem = useMemo(() => tabela.equipamentos
    .map((equipamento) => ({ ...equipamento, temperatura: equipamento.temperaturas[tamanho] }))
    .filter((equipamento): equipamento is typeof equipamento & { temperatura: number } => typeof equipamento.temperatura === "number" && equipamento.temperatura <= alvo)
    .sort((a, b) => b.temperatura - a.temperatura), [tabela, tamanho, alvo])

  const bau = tabela.tamanhos[tamanho]

  async function copiar() {
    const linhas = [
      `*Baú ${bau.codigo} (${String(bau.volume_m3).replace(".", ",")} m³) a ${grau(alvo)}* — equipamentos Carrier Transicold que atendem:`,
      ...atendem.map((e) => `• ${e.modelo} — chega a ${grau(e.temperatura)} (${e.acoplamento || e.linha})`),
      `Condição: ${tabela.condicao}`,
    ]
    try {
      await navigator.clipboard.writeText(linhas.join("\n"))
      setCopiado(true)
      onCopiado("Recomendação copiada. Cole no WhatsApp ou e-mail.")
      window.setTimeout(() => setCopiado(false), 2500)
    } catch {
      onCopiado("Não foi possível copiar neste aparelho.")
    }
  }

  return (
    <section className="rounded-3xl border border-cyan-900/70 bg-[#06182f] p-4 sm:p-5" aria-label="Tabela de aplicação">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.2em] text-cyan-400"><Snowflake size={14}/> Qual equipamento atende?</p>
        <Link href={documentoHref} className="inline-flex min-h-9 items-center gap-1.5 rounded-xl border border-cyan-700 px-3 text-xs font-semibold text-cyan-100"><FileText size={14}/> Tabela de aplicação</Link>
      </div>

      <p className="mt-3 text-sm font-semibold text-white">Tamanho do baú</p>
      <div className="mt-2 flex gap-2 overflow-x-auto pb-1" role="radiogroup" aria-label="Tamanho do baú">
        {tabela.tamanhos.map((item, indice) => (
          <button key={item.codigo} type="button" role="radio" aria-checked={tamanho === indice} onClick={() => setTamanho(indice)} className={`shrink-0 rounded-xl border px-3 py-2 text-left text-xs ${tamanho === indice ? "border-cyan-500 bg-cyan-950/60 text-cyan-100" : "border-[#24466f] text-slate-400"}`}>
            <span className="block font-bold">{item.codigo}</span>
            <span className="block text-[10px]">{String(item.volume_m3).replace(".", ",")} m³</span>
          </button>
        ))}
      </div>

      <p className="mt-3 text-sm font-semibold text-white">Temperatura que o cliente precisa</p>
      <div className="mt-2 flex flex-wrap gap-2" role="radiogroup" aria-label="Temperatura desejada">
        {TEMPERATURAS.map((valor) => (
          <button key={valor} type="button" role="radio" aria-checked={alvo === valor} onClick={() => setAlvo(valor)} className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${alvo === valor ? "border-cyan-500 bg-cyan-950/60 text-cyan-100" : "border-[#24466f] text-slate-400"}`}>{grau(valor)}</button>
        ))}
      </div>

      <div className="mt-4" aria-live="polite">
        {atendem.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-[#24466f] p-4 text-sm text-slate-400">Nenhum equipamento da tabela atende baú {bau.codigo} a {grau(alvo)}. {tabela.observacao}</p>
        ) : (
          <ul className="space-y-2" aria-label="Equipamentos que atendem">
            {atendem.map((equipamento) => (
              <li key={equipamento.modelo} className="flex items-center justify-between gap-3 rounded-2xl border border-[#163356] bg-[#081a32] px-4 py-3">
                <span className="min-w-0"><strong className="block text-white">{equipamento.modelo}</strong><span className="block text-xs text-slate-400">{equipamento.acoplamento}{equipamento.refrigerante ? ` · ${equipamento.refrigerante}` : ""}</span></span>
                <span className="shrink-0 text-right"><strong className="block text-cyan-200">{grau(equipamento.temperatura)}</strong><span className="block text-[10px] text-slate-500">mínima</span></span>
              </li>
            ))}
          </ul>
        )}
        {atendem.length > 0 && (
          <button type="button" onClick={() => void copiar()} className="mt-3 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-[#22466d] bg-[#0b2342] text-sm font-semibold text-cyan-200">
            {copiado ? <Check size={16}/> : <Copy size={16}/>} Copiar recomendação para WhatsApp
          </button>
        )}
        <p className="mt-2 text-[11px] leading-5 text-slate-500">{tabela.condicao}</p>
      </div>

      <details className="mt-3 rounded-2xl border border-[#163356] bg-[#050f22] p-3">
        <summary className="cursor-pointer text-sm font-semibold text-cyan-200">Ver tabela completa</summary>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-xs">
            <thead><tr className="text-left text-slate-400"><th className="p-2">Equipamento</th>{tabela.tamanhos.map((t) => <th key={t.codigo} className="p-2 text-center">{t.codigo}<span className="block font-normal">{String(t.volume_m3).replace(".", ",")} m³</span></th>)}</tr></thead>
            <tbody>
              {tabela.equipamentos.map((e) => (
                <tr key={e.modelo} className="border-t border-[#13203f]">
                  <td className="p-2 font-semibold text-white">{e.modelo}<span className="block font-normal text-slate-500">{e.acoplamento}</span></td>
                  {e.temperaturas.map((t, i) => <td key={i} className={`p-2 text-center ${t === null ? "text-slate-700" : "text-cyan-100"}`}>{t === null ? "—" : `${t}°`}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-[11px] text-slate-400">{tabela.premissas.map((p) => <li key={p}>{p}</li>)}</ul>
        <p className="mt-2 text-[11px] text-slate-400">{tabela.observacao}</p>
      </details>
    </section>
  )
}
