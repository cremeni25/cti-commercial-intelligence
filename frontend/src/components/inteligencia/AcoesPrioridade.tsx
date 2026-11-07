"use client"

import { useState, type FormEvent } from "react"
import { CalendarPlus, Check, Clock, Loader2, ThumbsDown } from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import {
  MOTIVOS_AJUSTE,
  TIPOS_PROXIMO_PASSO,
  agendarProximoPasso,
  ajustarSinal,
  concluirAtividadePrioridade,
  reagendarAtividadePrioridade,
  type PrioridadeComercial,
} from "@/services/inteligencia-comercial"

type Modo = "" | "agendar" | "reagendar" | "ajustar"

/** Data civil local (AAAA-MM-DD) daqui a N dias — sem conversão para UTC. */
export function dataLocal(dias: number) {
  const alvo = new Date()
  alvo.setDate(alvo.getDate() + dias)
  return `${alvo.getFullYear()}-${String(alvo.getMonth() + 1).padStart(2, "0")}-${String(alvo.getDate()).padStart(2, "0")}`
}

const botao = "inline-flex min-h-10 items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-semibold disabled:opacity-60"
const campo = "min-h-10 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-2 text-sm text-white"

/**
 * Resolve a prioridade sem sair da lista. Agendar/concluir/reagendar usam os
 * endpoints seguros de atividades do CRM; "não se aplica"/"adiar" só escondem o
 * alerta por um prazo e alimentam a calibração do agente — nada é apagado.
 */
export default function AcoesPrioridade({ item, onResolvido }: { item: PrioridadeComercial; onResolvido: (mensagem: string) => void }) {
  const { usuario } = useAuth()
  const [modo, setModo] = useState<Modo>("")
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const ehAtividade = item.entidade_tipo === "atividade"

  async function executar(acao: () => Promise<unknown>, mensagem: string) {
    setSalvando(true)
    setErro("")
    try {
      await acao()
      setModo("")
      onResolvido(mensagem)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir agora. Tente novamente.")
    } finally {
      setSalvando(false)
    }
  }

  function agendar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const dados = new FormData(evento.currentTarget)
    const data = String(dados.get("data") || "")
    void executar(() => agendarProximoPasso(item, {
      tipo: String(dados.get("tipo") || "LIGACAO"),
      data,
      titulo: String(dados.get("titulo") || "").trim() || `Próximo passo: ${item.cliente_nome}`,
      usuarioId: String(usuario?.id || ""),
    }), `Próximo passo agendado para ${data.split("-").reverse().join("/")}.`)
  }

  function reagendar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const data = String(new FormData(evento.currentTarget).get("data") || "")
    void executar(() => reagendarAtividadePrioridade(item, data), `Reagendado para ${data.split("-").reverse().join("/")}.`)
  }

  function ajustar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const dados = new FormData(evento.currentTarget)
    const decisao = String(dados.get("decisao")) === "ADIAR" ? "ADIAR" : "NAO_SE_APLICA"
    const adiarAte = String(dados.get("adiar_ate") || "")
    void executar(() => ajustarSinal(item, {
      decisao,
      motivo: String(dados.get("motivo") || "OUTRO"),
      observacao: String(dados.get("observacao") || ""),
      adiarAte: decisao === "ADIAR" ? adiarAte : undefined,
    }), decisao === "ADIAR" ? `Alerta adiado até ${adiarAte.split("-").reverse().join("/")}.` : "Alerta dispensado por 30 dias. Obrigado: isso calibra o agente.")
  }

  return (
    <div className="mt-3">
      <div className="flex flex-wrap gap-2">
        {ehAtividade ? (
          <>
            <button type="button" disabled={salvando} onClick={() => void executar(() => concluirAtividadePrioridade(item), "Atividade concluída.")} className={`${botao} border-emerald-700 bg-emerald-950/40 text-emerald-200`}>
              {salvando && !modo ? <Loader2 size={14} className="animate-spin"/> : <Check size={14}/>} Concluir
            </button>
            <button type="button" aria-expanded={modo === "reagendar"} onClick={() => setModo(modo === "reagendar" ? "" : "reagendar")} className={`${botao} border-[#24466f] text-cyan-200`}><Clock size={14}/> Reagendar</button>
          </>
        ) : (
          <button type="button" aria-expanded={modo === "agendar"} onClick={() => setModo(modo === "agendar" ? "" : "agendar")} className={`${botao} border-cyan-700 bg-cyan-950/40 text-cyan-100`}><CalendarPlus size={14}/> Agendar próximo passo</button>
        )}
        <button type="button" aria-expanded={modo === "ajustar"} onClick={() => setModo(modo === "ajustar" ? "" : "ajustar")} className={`${botao} border-[#24466f] text-slate-300`}><ThumbsDown size={14}/> Não se aplica / adiar</button>
      </div>

      {modo === "agendar" && (
        <form onSubmit={agendar} className="mt-3 grid gap-2 rounded-2xl border border-[#163356] bg-[#06142a] p-3 sm:grid-cols-[140px_160px_1fr_auto]">
          <select name="tipo" aria-label="Tipo de contato" defaultValue="LIGACAO" className={campo}>{TIPOS_PROXIMO_PASSO.map((tipo) => <option key={tipo.valor} value={tipo.valor}>{tipo.rotulo}</option>)}</select>
          <input type="date" name="data" aria-label="Data do próximo passo" required min={dataLocal(0)} defaultValue={dataLocal(1)} className={campo}/>
          <input name="titulo" aria-label="Assunto" placeholder={`Retorno com ${item.cliente_nome}`} maxLength={140} className={campo}/>
          <button type="submit" disabled={salvando} className={`${botao} justify-center border-cyan-500 bg-cyan-500 text-slate-950`}>{salvando ? <Loader2 size={14} className="animate-spin"/> : <Check size={14}/>} Agendar</button>
        </form>
      )}

      {modo === "reagendar" && (
        <form onSubmit={reagendar} className="mt-3 flex flex-wrap gap-2 rounded-2xl border border-[#163356] bg-[#06142a] p-3">
          <input type="date" name="data" aria-label="Nova data" required min={dataLocal(0)} defaultValue={dataLocal(1)} className={`${campo} max-w-48`}/>
          <button type="submit" disabled={salvando} className={`${botao} border-cyan-500 bg-cyan-500 text-slate-950`}>{salvando ? <Loader2 size={14} className="animate-spin"/> : <Check size={14}/>} Salvar data</button>
        </form>
      )}

      {modo === "ajustar" && (
        <form onSubmit={ajustar} className="mt-3 grid gap-2 rounded-2xl border border-[#163356] bg-[#06142a] p-3">
          <fieldset className="flex flex-wrap gap-3 text-sm text-slate-300">
            <legend className="sr-only">Decisão</legend>
            <label className="flex items-center gap-2"><input type="radio" name="decisao" value="NAO_SE_APLICA" defaultChecked/> Não se aplica</label>
            <label className="flex items-center gap-2"><input type="radio" name="decisao" value="ADIAR"/> Adiar até</label>
            <input type="date" name="adiar_ate" aria-label="Adiar até" min={dataLocal(1)} defaultValue={dataLocal(7)} className={`${campo} max-w-44`}/>
          </fieldset>
          <select name="motivo" aria-label="Motivo" defaultValue="JA_TRATADO" className={campo}>{MOTIVOS_AJUSTE.map((motivo) => <option key={motivo.valor} value={motivo.valor}>{motivo.rotulo}</option>)}</select>
          <input name="observacao" aria-label="Observação" placeholder="Observação (opcional)" maxLength={500} className={campo}/>
          <button type="submit" disabled={salvando} className={`${botao} justify-center border-slate-500 bg-slate-800 text-white`}>{salvando ? <Loader2 size={14} className="animate-spin"/> : <Check size={14}/>} Confirmar</button>
        </form>
      )}

      {erro && <p role="alert" className="mt-2 rounded-xl border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-200">{erro}</p>}
    </div>
  )
}
