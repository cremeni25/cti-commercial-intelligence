"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Archive, Download, Loader2, ShieldCheck, UserX } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { listarUsuarios } from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI } from "@/modules/usuarios/types/usuario.types"
import {
  buscarBackups,
  buscarCarteiras,
  gerarBackup,
  transferirCarteira,
  type BackupAcervo,
  type PessoaCarteira,
  type ResumoCarteiras,
} from "@/services/acervo-comercial"

const numero = (valor: number) => valor.toLocaleString("pt-BR")
function dataHora(valor?: string) {
  if (!valor) return "—"
  const data = new Date(valor)
  return Number.isNaN(data.getTime()) ? "—" : data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo" })
}

function Transferir({ pessoa, destinos, onFeito }: { pessoa: PessoaCarteira; destinos: UsuarioCTI[]; onFeito: (texto: string) => void }) {
  const [para, setPara] = useState("")
  const [motivo, setMotivo] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")
  const opcoes = destinos.filter((d) => d.id !== pessoa.usuario_id)

  async function enviar() {
    const destino = opcoes.find((d) => d.id === para)
    if (!destino) return setErro("Escolha quem vai assumir a carteira.")
    if (!window.confirm(`Transferir para ${destino.nome} os ${pessoa.clientes} clientes, ${pessoa.negocios_abertos} negócios em aberto e ${pessoa.atividades_pendentes} atividades pendentes de ${pessoa.nome}? Visitas feitas e negócios encerrados continuam no nome de ${pessoa.nome}.`)) return
    setEnviando(true); setErro("")
    try {
      const r = await transferirCarteira(pessoa.usuario_id, para, motivo)
      onFeito(`Carteira de ${pessoa.nome} transferida para ${destino.nome}: ${r.clientes} clientes, ${r.negocios_abertos} negócios em aberto e ${r.atividades_pendentes} atividades pendentes. ${r.historico_preservado} registros do histórico continuaram com o autor original. Cópia de segurança feita antes.`)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível transferir.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
      <select aria-label={`Quem assume a carteira de ${pessoa.nome}`} value={para} onChange={(e) => setPara(e.target.value)} className="min-h-10 rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm">
        <option value="">Quem assume?</option>
        {opcoes.map((d) => <option key={d.id} value={d.id}>{d.nome}</option>)}
      </select>
      <input value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder="Motivo (opcional)" maxLength={300} aria-label="Motivo da transferência" className="min-h-10 rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm"/>
      <button type="button" disabled={enviando} onClick={() => void enviar()} className="min-h-10 rounded-xl bg-cyan-500 px-4 text-sm font-bold text-slate-950 disabled:opacity-60">{enviando ? "Transferindo..." : "Transferir carteira"}</button>
      {erro && <p role="alert" className="text-sm text-red-300 sm:col-span-3">{erro}</p>}
    </div>
  )
}

export default function AcervoPage() {
  const [resumo, setResumo] = useState<ResumoCarteiras | null>(null)
  const [backups, setBackups] = useState<BackupAcervo[] | null>(null)
  const [usuarios, setUsuarios] = useState<UsuarioCTI[]>([])
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [exportando, setExportando] = useState(false)

  const carregar = useCallback(async () => {
    setErro("")
    const [r, b, u] = await Promise.allSettled([buscarCarteiras(), buscarBackups(), listarUsuarios()])
    if (r.status === "fulfilled") setResumo(r.value); else setErro(r.reason instanceof Error ? r.reason.message : "Não foi possível carregar as carteiras.")
    setBackups(b.status === "fulfilled" ? b.value : [])
    if (u.status === "fulfilled") setUsuarios(u.value)
  }, [])

  useEffect(() => {
    let ativo = true
    void Promise.allSettled([buscarCarteiras(), buscarBackups(), listarUsuarios()]).then(([r, b, u]) => {
      if (!ativo) return
      if (r.status === "fulfilled") setResumo(r.value); else setErro(r.reason instanceof Error ? r.reason.message : "Não foi possível carregar as carteiras.")
      setBackups(b.status === "fulfilled" ? b.value : [])
      if (u.status === "fulfilled") setUsuarios(u.value)
    })
    return () => { ativo = false }
  }, [])

  const destinos = useMemo(() => usuarios.filter((u) => u.ativo && u.id && u.nome).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")), [usuarios])
  const paradas = resumo?.pessoas.filter((p) => !p.ativo && (p.clientes || p.negocios_abertos || p.atividades_pendentes)) || []
  const ativas = resumo?.pessoas.filter((p) => p.ativo) || []

  async function exportar() {
    setExportando(true); setErro(""); setMensagem("")
    try {
      const copia = await gerarBackup()
      if (copia.url) window.open(copia.url, "_blank", "noopener")
      setMensagem("Cópia completa gerada e guardada no cofre. O download foi aberto em outra aba.")
      setBackups((atual) => [copia, ...(atual || [])])
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível gerar a cópia.")
    } finally {
      setExportando(false)
    }
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar/>
      <section className="min-w-0 flex-1">
        <Topbar/>
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">Gestão</p>
            <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Acervo comercial</h1>
            <p className="mt-2 max-w-3xl text-gray-400">O histórico é da empresa, não de quem o registrou. Aqui ficam as carteiras de quem saiu, a transferência para quem assume e as cópias de segurança de tudo.</p>
          </header>

          {mensagem && <p role="status" className="rounded-2xl border border-emerald-800 bg-emerald-950/30 px-5 py-4 text-sm text-emerald-200">{mensagem}</p>}
          {erro && <p role="alert" className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</p>}

          {!resumo && !erro ? <div className="grid min-h-40 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : resumo && (
            <>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-[#163356] bg-[#081a32] p-4"><p className="text-xs uppercase text-slate-500">Carteiras paradas</p><strong className="mt-1 block text-2xl text-amber-300">{numero(resumo.carteiras_paradas)}</strong><span className="text-xs text-slate-400">de pessoas desativadas</span></div>
                <div className="rounded-2xl border border-[#163356] bg-[#081a32] p-4"><p className="text-xs uppercase text-slate-500">Clientes sem responsável</p><strong className="mt-1 block text-2xl text-white">{numero(resumo.clientes_sem_responsavel)}</strong><span className="text-xs text-slate-400">ficam com a gestão</span></div>
                <div className="rounded-2xl border border-[#163356] bg-[#081a32] p-4"><p className="text-xs uppercase text-slate-500">Última cópia de segurança</p><strong className="mt-1 block text-lg text-white">{dataHora(backups?.[0]?.criado_em)}</strong><span className="text-xs text-slate-400">automática todo domingo</span></div>
              </div>

              <section aria-label="Carteiras de quem saiu" className="rounded-3xl border border-[#13203f] bg-[#061126] p-5">
                <h2 className="flex items-center gap-2 text-lg font-semibold"><UserX size={20} className="text-amber-300"/> Carteiras de quem saiu</h2>
                <p className="mt-1 text-sm text-slate-400">A transferência leva só o que está em aberto. Visitas feitas e negócios ganhos ou perdidos continuam no nome de quem os fez.</p>
                {paradas.length === 0 ? <p className="mt-4 text-sm text-emerald-300">Nenhuma carteira parada. Todo o trabalho em aberto tem um responsável ativo.</p> : (
                  <ul className="mt-4 space-y-3">
                    {paradas.map((p) => (
                      <li key={p.usuario_id} className="rounded-2xl border border-amber-900/50 bg-[#0b1d38] p-4">
                        <div className="flex flex-wrap items-baseline justify-between gap-2"><strong>{p.nome}</strong><span className="text-xs text-slate-400">{p.email}</span></div>
                        <p className="mt-1 text-sm text-slate-300">{numero(p.clientes)} clientes · {numero(p.negocios_abertos)} negócios em aberto · {numero(p.atividades_pendentes)} atividades pendentes</p>
                        <Transferir pessoa={p} destinos={destinos} onFeito={(texto) => { setMensagem(texto); void carregar() }}/>
                      </li>
                    ))}
                  </ul>
                )}
                {ativas.length > 0 && (
                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm font-semibold text-cyan-200">Ver carteiras ativas ({ativas.length})</summary>
                    <ul className="mt-3 divide-y divide-[#13203f] text-sm">
                      {ativas.map((p) => <li key={p.usuario_id} className="flex flex-wrap justify-between gap-2 py-2"><span>{p.nome}</span><span className="text-slate-400">{numero(p.clientes)} clientes · {numero(p.negocios_abertos)} negócios · {numero(p.atividades_pendentes)} atividades</span></li>)}
                    </ul>
                  </details>
                )}
              </section>
            </>
          )}

          <section aria-label="Cópias de segurança" className="rounded-3xl border border-[#13203f] bg-[#061126] p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="flex items-center gap-2 text-lg font-semibold"><ShieldCheck size={20} className="text-emerald-300"/> Cópias de segurança</h2>
                <p className="mt-1 text-sm text-slate-400">Planilha com clientes, negócios, propostas, pedidos, atividades, vendas, feiras, histórico de responsáveis e as planilhas comerciais. Feita sozinha todo domingo e antes de cada transferência.</p>
              </div>
              <button type="button" disabled={exportando} onClick={() => void exportar()} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-cyan-500 px-4 text-sm font-bold text-slate-950 disabled:opacity-60">{exportando ? <><Loader2 size={16} className="animate-spin"/> Gerando...</> : <><Download size={16}/> Exportar agora</>}</button>
            </div>
            {backups === null ? <Loader2 className="mt-4 animate-spin text-cyan-300"/> : backups.length === 0 ? <p className="mt-4 text-sm text-slate-400">Nenhuma cópia ainda. A primeira será feita no domingo, ou agora pelo botão acima.</p> : (
              <ul className="mt-4 divide-y divide-[#13203f] text-sm">
                {backups.map((b) => (
                  <li key={b.arquivo} className="flex flex-wrap items-center justify-between gap-2 py-2">
                    <span className="flex items-center gap-2"><Archive size={16} className="text-slate-500"/>{dataHora(b.criado_em)} <span className="text-slate-500">· {b.motivo}</span></span>
                    {b.url ? <a href={b.url} target="_blank" rel="noreferrer" className="text-cyan-300 underline">Baixar</a> : <span className="text-slate-500">link indisponível</span>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}
