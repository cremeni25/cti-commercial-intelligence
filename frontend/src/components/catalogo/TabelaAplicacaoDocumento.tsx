"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { ArrowLeft, Loader2, Printer, Share2 } from "lucide-react"
import { buscarVitrineCatalogo, type TabelaAplicacao } from "@/services/inteligencia-comercial"

/**
 * Tabela de aplicação como documento, gerada pelo próprio CTI a partir dos dados
 * oficiais — não depende de PDF anexado. "Salvar em PDF" usa a impressão do
 * navegador (layout claro, só a tabela); "Compartilhar" usa o menu nativo do
 * aparelho (WhatsApp, e-mail…).
 */
export default function TabelaAplicacaoDocumento({ voltar }: { voltar: string }) {
  const [tabela, setTabela] = useState<TabelaAplicacao | null>(null)
  const [erro, setErro] = useState("")
  const [aviso, setAviso] = useState("")

  useEffect(() => {
    let ativo = true
    buscarVitrineCatalogo()
      .then((dados) => {
        if (!ativo) return
        if (dados.tabela_aplicacao) setTabela(dados.tabela_aplicacao)
        else setErro("Tabela de aplicação indisponível no momento.")
      })
      .catch((falha: unknown) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar a tabela.") })
    return () => { ativo = false }
  }, [])

  async function compartilhar() {
    const dados = { title: "Tabela de aplicação Carrier · Viena", text: "Tabela de aplicação: equipamento x tamanho do baú x temperatura.", url: window.location.href }
    try {
      if (navigator.share) {
        await navigator.share(dados)
        return
      }
      await navigator.clipboard.writeText(dados.url)
      setAviso("Link copiado. Cole no WhatsApp ou e-mail.")
    } catch {
      /* compartilhamento cancelado pela pessoa */
    }
  }

  if (erro) return <p className="m-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</p>
  if (!tabela) return <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>

  return (
    <article className="mx-auto max-w-5xl px-4 py-5 text-white sm:px-6 print:max-w-none print:px-0 print:py-0 print:text-black" aria-label="Documento da tabela de aplicação">
      <div className="mb-4 flex flex-wrap items-center gap-2 print:hidden">
        <Link href={voltar} aria-label="Voltar ao catálogo" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
        <button type="button" onClick={() => void compartilhar()} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-cyan-700 px-4 text-sm font-semibold text-cyan-200"><Share2 size={16}/> Compartilhar</button>
        <button type="button" onClick={() => window.print()} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-cyan-500 px-4 text-sm font-bold text-slate-950"><Printer size={16}/> Salvar em PDF / Imprimir</button>
        {aviso && <span role="status" className="text-sm text-emerald-300">{aviso}</span>}
      </div>

      <header className="rounded-2xl bg-[#0b2a5b] px-4 py-3 print:rounded-none print:bg-[#0b2a5b] print:text-white">
        <p className="text-xs uppercase tracking-[.2em] text-cyan-200">Carrier Transicold · Viena Refrigeração</p>
        <h1 className="mt-1 text-2xl font-black">TABELA DE APLICAÇÃO</h1>
      </header>
      <p className="mt-3 text-sm font-semibold">Considerar temperatura para baús novos</p>
      <p className="text-xs text-slate-400 print:text-gray-600">{tabela.condicao}</p>

      <div className="mt-3 overflow-x-auto rounded-2xl border border-[#163356] print:overflow-visible print:rounded-none print:border-gray-400">
        <table className="w-full min-w-[760px] border-collapse text-xs print:min-w-0">
          <thead>
            <tr className="bg-[#0b1d38] text-left text-slate-300 print:bg-gray-200 print:text-black">
              <th className="p-2">Equipamento</th><th className="p-2">Refrig.</th><th className="p-2">Acoplamento</th><th className="p-2">Isolamento</th>
              {tabela.tamanhos.map((t) => <th key={t.codigo} className="p-2 text-center">{t.codigo}<span className="block font-normal">{String(t.volume_m3).replace(".", ",")} m³</span></th>)}
            </tr>
          </thead>
          <tbody>
            {tabela.equipamentos.map((e) => (
              <tr key={e.modelo} className="border-t border-[#163356] print:border-gray-300">
                <td className="p-2 font-bold">{e.modelo}</td>
                <td className="p-2">{e.refrigerante || "—"}</td>
                <td className="p-2">{e.acoplamento || "—"}</td>
                <td className="p-2">{e.isolamento_mm ? `${e.isolamento_mm} mm` : "—"}</td>
                {e.temperaturas.map((t, i) => <td key={i} className={`p-2 text-center font-semibold ${t === null ? "bg-[#06111f] text-slate-700 print:bg-gray-100 print:text-gray-400" : "text-cyan-100 print:text-black"}`}>{t === null ? "—" : `${t} °C`}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <section className="mt-4">
        <h2 className="text-sm font-bold">Premissas da simulação Carrier</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-300 print:text-gray-700">{tabela.premissas.map((p) => <li key={p}>{p}</li>)}</ul>
        <p className="mt-3 text-xs font-semibold">{tabela.observacao}</p>
      </section>
    </article>
  )
}
