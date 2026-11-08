"use client"

import { useEffect, useState } from "react"
import { FileSpreadsheet, Loader2, Upload } from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import { buscarResumoPlanilhas, enviarPlanilhasComerciais, type ResumoPlanilhasComerciais } from "@/services/inteligencia-comercial"

function dataHora(valor?: string | null) {
  if (!valor) return ""
  const data = new Date(valor)
  return Number.isNaN(data.getTime()) ? "" : data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo" })
}

const numero = (valor?: number) => (valor ?? 0).toLocaleString("pt-BR")

/**
 * Master envia o funil de vendas e a planilha NEGOCIAÇÕES; o CTI lê, guarda no
 * cofre privado e a IA Comercial passa a usar. Ponte até a leitura automática
 * do SharePoint.
 */
export default function PlanilhasComerciaisCard() {
  const { usuario } = useAuth()
  const master = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"
  const [resumo, setResumo] = useState<ResumoPlanilhasComerciais | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [mensagem, setMensagem] = useState<{ tom: "ok" | "erro"; texto: string } | null>(null)

  useEffect(() => {
    if (!master) return
    let ativo = true
    buscarResumoPlanilhas().then((dados) => { if (ativo) setResumo(dados) }).catch(() => { if (ativo) setResumo({ disponivel: false }) })
    return () => { ativo = false }
  }, [master])

  if (!master) return null

  async function enviar(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const formulario = evento.currentTarget
    const arquivo = (nome: string) => (formulario.elements.namedItem(nome) as HTMLInputElement | null)?.files?.[0] || null
    const funil = arquivo("funil")
    const negociacoes = arquivo("negociacoes")
    if (!funil && !negociacoes) {
      setMensagem({ tom: "erro", texto: "Escolha ao menos uma planilha." })
      return
    }
    setEnviando(true)
    setMensagem(null)
    try {
      const novo = await enviarPlanilhasComerciais({ funil, negociacoes })
      setResumo(novo)
      formulario.reset()
      setMensagem({ tom: "ok", texto: "Planilhas lidas. A IA Comercial já usa os dados novos." })
    } catch (falha) {
      setMensagem({ tom: "erro", texto: falha instanceof Error ? falha.message : "Não foi possível enviar." })
    } finally {
      setEnviando(false)
    }
  }

  const arquivo = (tipo: string) => resumo?.arquivos?.find((item) => item.tipo === tipo)
  const funil = arquivo("FUNIL_VENDAS")
  const negociacoes = arquivo("NEGOCIACOES")

  return (
    <section aria-label="Planilhas comerciais" className="rounded-3xl border border-[#13203f] bg-[#061126] p-4 sm:p-5">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-white"><FileSpreadsheet size={20} className="text-cyan-400"/> Planilhas comerciais</h2>
      <p className="mt-1 text-sm text-slate-400">Funil de vendas e NEGOCIAÇÕES alimentam a IA Comercial. Envie a versão mais nova sempre que quiser.</p>

      {resumo === null ? (
        <div className="mt-3"><Loader2 size={18} className="animate-spin text-cyan-300"/></div>
      ) : resumo.disponivel && resumo.totais ? (
        <ul className="mt-3 grid gap-2 text-sm sm:grid-cols-3" aria-label="O que a IA já leu">
          <li className="rounded-2xl border border-[#163356] bg-[#081a32] px-3 py-2"><strong className="block text-white">{numero(resumo.totais.funil_vendas_atual)}</strong><span className="text-xs text-slate-400">registros do funil{funil?.enviado_em ? ` · ${dataHora(funil.enviado_em)}` : ""}</span></li>
          <li className="rounded-2xl border border-[#163356] bg-[#081a32] px-3 py-2"><strong className="block text-white">{numero(resumo.totais.negociacoes_andamento)}</strong><span className="text-xs text-slate-400">negociações{negociacoes?.enviado_em ? ` · ${dataHora(negociacoes.enviado_em)}` : ""}</span></li>
          <li className="rounded-2xl border border-[#163356] bg-[#081a32] px-3 py-2"><strong className="block text-white">{numero(resumo.totais.vendas_realizadas)}</strong><span className="text-xs text-slate-400">vendas realizadas</span></li>
        </ul>
      ) : (
        <p className="mt-3 rounded-2xl border border-dashed border-amber-800 p-3 text-sm text-amber-200">A IA ainda não recebeu as planilhas. Envie abaixo.</p>
      )}

      <form onSubmit={enviar} className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
        <label className="grid gap-1 text-xs font-semibold text-slate-300">Funil de vendas (.xlsx)
          <input name="funil" type="file" accept=".xlsx,.xlsm" className="text-xs font-normal text-slate-300"/>
        </label>
        <label className="grid gap-1 text-xs font-semibold text-slate-300">NEGOCIAÇÕES (.xlsx)
          <input name="negociacoes" type="file" accept=".xlsx,.xlsm" className="text-xs font-normal text-slate-300"/>
        </label>
        <button type="submit" disabled={enviando} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 text-sm font-bold text-slate-950 disabled:opacity-60">
          {enviando ? <><Loader2 size={16} className="animate-spin"/> Lendo planilhas...</> : <><Upload size={16}/> Enviar planilhas</>}
        </button>
      </form>
      {mensagem && <p role="status" className={`mt-3 text-sm ${mensagem.tom === "ok" ? "text-emerald-300" : "text-red-300"}`}>{mensagem.texto}</p>}
    </section>
  )
}
