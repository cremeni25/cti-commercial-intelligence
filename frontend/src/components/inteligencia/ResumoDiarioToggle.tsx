"use client"

import { useEffect, useState } from "react"
import { Bell, BellOff, Loader2, Send } from "lucide-react"
import {
  ativarResumoDiario,
  desativarResumoDiario,
  ehIphoneSemInstalar,
  enviarNotificacaoTeste,
  situacaoAtualPush,
  type SituacaoPush,
} from "@/services/notificacoes-push"

const EXPLICACAO: Partial<Record<SituacaoPush, string>> = {
  sem_suporte: "Este navegador não recebe notificações. No Android, use o Chrome; no iPhone, instale o app na tela de início.",
  servidor_inativo: "O resumo no celular está sendo ativado no servidor e aparecerá aqui em breve.",
  bloqueado: "As notificações do CTI estão bloqueadas neste aparelho. Libere nas configurações do navegador para ativar.",
}

/** Liga/desliga o resumo diário (dias úteis, de manhã) neste aparelho. */
export default function ResumoDiarioToggle() {
  const [situacao, setSituacao] = useState<SituacaoPush>("carregando")
  const [ocupado, setOcupado] = useState(false)
  const [mensagem, setMensagem] = useState("")
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    situacaoAtualPush().then((atual) => { if (ativo) setSituacao(atual) }).catch(() => { if (ativo) setSituacao("servidor_inativo") })
    return () => { ativo = false }
  }, [])

  async function executar(acao: () => Promise<unknown>, sucesso: string, proxima?: SituacaoPush) {
    setOcupado(true)
    setErro("")
    setMensagem("")
    try {
      await acao()
      setMensagem(sucesso)
      if (proxima) setSituacao(proxima)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir agora.")
      setSituacao(await situacaoAtualPush().catch(() => "inativo" as SituacaoPush))
    } finally {
      setOcupado(false)
    }
  }

  if (situacao === "carregando") return null
  const iphone = situacao === "sem_suporte" && ehIphoneSemInstalar()

  return (
    <section className="mb-5 rounded-3xl border border-[#163356] bg-[#061126] p-4" aria-label="Resumo diário no celular">
      <div className="flex items-start gap-3">
        <span className={`grid size-10 shrink-0 place-items-center rounded-xl ${situacao === "ativo" ? "bg-emerald-950/60 text-emerald-300" : "bg-[#0b2342] text-cyan-300"}`}>{situacao === "ativo" ? <Bell size={18}/> : <BellOff size={18}/>}</span>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-white">Resumo diário no celular</p>
          <p className="mt-1 text-sm leading-6 text-slate-400">
            {situacao === "ativo"
              ? "Ativado. Nos dias úteis, pela manhã, você recebe por onde começar o dia."
              : iphone
                ? "No iPhone: toque em Compartilhar › Adicionar à Tela de Início, abra o CTI pelo ícone e ative aqui."
                : EXPLICACAO[situacao] || "Receba nos dias úteis, pela manhã, a primeira prioridade do seu dia — sem valores na tela bloqueada."}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {situacao === "inativo" && (
              <button type="button" disabled={ocupado} onClick={() => void executar(ativarResumoDiario, "Pronto! Enviamos a próxima leitura amanhã cedo.", "ativo")} className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2 text-sm font-bold text-slate-950 disabled:opacity-60">
                {ocupado ? <Loader2 size={16} className="animate-spin"/> : <Bell size={16}/>} Ativar resumo diário
              </button>
            )}
            {situacao === "ativo" && (
              <>
                <button type="button" disabled={ocupado} onClick={() => void executar(enviarNotificacaoTeste, "Notificação de teste enviada para este aparelho.")} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-200 disabled:opacity-60"><Send size={14}/> Enviar teste</button>
                <button type="button" disabled={ocupado} onClick={() => void executar(desativarResumoDiario, "Resumo diário desativado neste aparelho.", "inativo")} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-[#24466f] px-3 py-2 text-xs font-semibold text-slate-300 disabled:opacity-60"><BellOff size={14}/> Desativar</button>
              </>
            )}
          </div>
          {mensagem && <p role="status" className="mt-2 text-sm text-emerald-300">{mensagem}</p>}
          {erro && <p role="alert" className="mt-2 text-sm text-red-300">{erro}</p>}
        </div>
      </div>
    </section>
  )
}
