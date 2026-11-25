"use client"

import { useEffect, useMemo, useState } from "react"
import { BadgeDollarSign, Download, FileText, Handshake, Loader2, Plus, Printer, Users, X } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { listarUsuarios } from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI } from "@/modules/usuarios/types/usuario.types"
import { buscarNoCTI, type ResultadoBusca } from "@/services/assistente-cti"
import {
  atualizarIndicacao,
  baixarExtratoCsv,
  buscarAcesso,
  buscarExtrato,
  buscarIndicacoes,
  buscarIndicadores,
  buscarPainel,
  registrarIndicacao,
  salvarIndicador,
  ROTULO_COMISSAO,
  ROTULO_LINHA,
  ROTULO_STATUS,
  type Acesso,
  type Agregado,
  type Extrato,
  type Indicacao,
  type Indicador,
  type Linha,
  type Painel,
  type Periodo,
  type StatusIndicacao,
} from "@/services/indicacoes"

const moeda = (v: number | null | undefined) => (v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 })
const numero = (v: number | null | undefined) => (v || 0).toLocaleString("pt-BR")
const pct = (v: number | null | undefined) => (v === null || v === undefined ? "—" : `${(v * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`)
const data = (v?: string | null) => (v ? v.slice(0, 10).split("-").reverse().join("/") : "—")
const LINHAS: Linha[] = ["TRAILER", "DIESEL TRUCK", "DIRECT DRIVE"]
const MESES = ["Ano inteiro", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
const COR_STATUS: Record<StatusIndicacao, string> = {
  INDICADA: "border-slate-600 text-slate-200",
  EM_NEGOCIACAO: "border-cyan-700 text-cyan-200",
  VENDIDA: "border-emerald-700 text-emerald-200",
  PERDIDA: "border-red-900 text-red-200",
}
const caixa = "rounded-3xl border border-[#13203f] bg-[#061126] p-5"
const campoBase = "min-h-10 rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm text-white"
const campo = `${campoBase} w-full`
const botao = "inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-4 text-sm font-bold disabled:opacity-50"

function Cartao({ titulo, valor, detalhe, destaque }: { titulo: string; valor: string; detalhe?: string; destaque?: string }) {
  return (
    <div className="rounded-2xl border border-[#163356] bg-[#081a32] p-4">
      <p className="text-xs uppercase text-slate-500">{titulo}</p>
      <strong className={`mt-1 block text-2xl ${destaque || "text-white"}`}>{valor}</strong>
      {detalhe && <span className="text-xs text-slate-400">{detalhe}</span>}
    </div>
  )
}

function Seletor({ periodo, onMudar }: { periodo: Periodo; onMudar: (p: Periodo) => void }) {
  const anoAtual = new Date().getFullYear()
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Período">
      <select aria-label="Ano" value={periodo.ano || ""} onChange={(e) => onMudar({ ano: e.target.value ? Number(e.target.value) : undefined, mes: e.target.value ? periodo.mes : undefined })} className={campoBase}>
        <option value="">Todo o histórico</option>
        {[anoAtual, anoAtual - 1, anoAtual - 2].map((a) => <option key={a} value={a}>{a}</option>)}
      </select>
      {periodo.ano && (
        <select aria-label="Mês" value={periodo.mes || 0} onChange={(e) => onMudar({ ...periodo, mes: Number(e.target.value) || undefined })} className={campoBase}>
          {MESES.map((m, i) => <option key={m} value={i}>{m}</option>)}
        </select>
      )}
    </div>
  )
}

function TabelaAgregado<T extends Agregado>({ titulo, linhas, rotulo, onAbrir, extra }: { titulo: string; linhas: T[]; rotulo: (l: T) => string; onAbrir?: (l: T) => void; extra?: (l: T) => string }) {
  return (
    <section aria-label={titulo} className={caixa}>
      <h2 className="text-lg font-semibold">{titulo}</h2>
      {linhas.length === 0 ? <p className="mt-2 text-sm text-slate-400">Sem indicações no período.</p> : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">{titulo.split(" ").pop()}</th><th>Indicações</th><th>Vendidas</th><th>Conversão</th><th>Equip.</th><th>Valor vendido</th><th>Comissão</th><th>A pagar</th>{extra && <th>Peso</th>}</tr></thead>
            <tbody>
              {linhas.map((l) => (
                <tr key={rotulo(l)} className="border-t border-[#13203f]">
                  <td className="py-2 font-semibold">{onAbrir ? <button type="button" onClick={() => onAbrir(l)} className="text-left text-cyan-300 underline-offset-2 hover:underline">{rotulo(l)}</button> : rotulo(l)}</td>
                  <td>{numero(l.indicacoes)}</td><td>{numero(l.vendidas)}</td><td>{pct(l.conversao)}</td><td>{numero(l.equipamentos_vendidos)}</td>
                  <td>{moeda(l.valor_vendido)}</td><td>{moeda(l.comissao_total)}</td><td className="text-amber-200">{moeda(l.comissao_a_pagar + l.comissao_nf_recebida)}</td>
                  {extra && <td>{extra(l)}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function ExtratoModal({ indicadorId, periodo, onFechar }: { indicadorId: string; periodo: Periodo; onFechar: () => void }) {
  const [dados, setDados] = useState<Extrato | null>(null)
  const [erro, setErro] = useState("")
  useEffect(() => {
    let ativo = true
    buscarExtrato(indicadorId, periodo).then((d) => { if (ativo) setDados(d) }).catch((e: unknown) => { if (ativo) setErro(e instanceof Error ? e.message : "Falha ao abrir o extrato.") })
    return () => { ativo = false }
  }, [indicadorId, periodo])
  return (
    <div role="dialog" aria-modal="true" aria-label="Extrato do indicador" className="fixed inset-0 z-50 flex justify-end bg-black/60 print:static print:bg-white">
      <section className="h-full w-full max-w-3xl overflow-y-auto border-l border-[#163356] bg-[#061126] p-5 print:max-w-none print:border-0 print:bg-white print:text-black">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[.2em] text-cyan-400">Relatório individual</p>
            <h2 className="mt-1 text-2xl font-bold">{dados?.indicador.nome || "Indicador"}</h2>
            <p className="text-sm text-slate-400">{periodo.ano ? `${periodo.mes ? `${MESES[periodo.mes]} de ` : ""}${periodo.ano}` : "Todo o histórico"}{dados?.indicador.documento ? ` · documento ${dados.indicador.documento}` : ""}</p>
          </div>
          <div className="flex gap-2 print:hidden">
            <button type="button" onClick={() => void baixarExtratoCsv(indicadorId, periodo).catch((e: unknown) => setErro(e instanceof Error ? e.message : "Falha no download."))} className={`${botao} border border-[#24466f]`}><Download size={16}/>Planilha</button>
            <button type="button" onClick={() => window.print()} className={`${botao} border border-[#24466f]`}><Printer size={16}/>Imprimir</button>
            <button type="button" onClick={onFechar} aria-label="Fechar extrato" className="rounded-xl border border-[#24466f] p-2"><X size={18}/></button>
          </div>
        </div>
        {erro && <p role="alert" className="mt-4 text-sm text-red-300">{erro}</p>}
        {!dados && !erro && <div className="grid min-h-40 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
        {dados && (
          <>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <Cartao titulo="Vendas concluídas" valor={numero(dados.resumo.vendidas)} detalhe={`${numero(dados.resumo.equipamentos_vendidos)} equipamentos · ${moeda(dados.resumo.valor_vendido)}`}/>
              <Cartao titulo="Comissão a receber" valor={moeda(dados.resumo.comissao_a_pagar + dados.resumo.comissao_nf_recebida)} detalhe={`${moeda(dados.resumo.comissao_nf_recebida)} com NF recebida`} destaque="text-amber-300"/>
              <Cartao titulo="Comissão paga" valor={moeda(dados.resumo.comissao_paga)} destaque="text-emerald-300"/>
            </div>
            <ul className="mt-4 divide-y divide-[#13203f]">
              {dados.indicacoes.map((i) => (
                <li key={i.id} className="py-3 text-sm">
                  <p className="flex flex-wrap items-center justify-between gap-2"><strong>{i.cliente_nome}</strong><span className={`rounded-full border px-2 py-0.5 text-[11px] ${COR_STATUS[i.status]}`}>{ROTULO_STATUS[i.status]}</span></p>
                  <p className="text-xs text-slate-400">{[i.regiao, `${i.quantidade}× ${ROTULO_LINHA[i.linha]}${i.modelo ? ` ${i.modelo}` : ""}`, moeda(i.valor_final), `indicada em ${data(i.data_indicacao)}`, i.data_venda && `vendida em ${data(i.data_venda)}`].filter(Boolean).join(" · ")}</p>
                  {i.comissao_valor ? <p className="text-xs text-amber-200">Comissão {moeda(i.comissao_valor)} ({i.quantidade} × {moeda(i.comissao_unitaria)}) · {i.comissao_status && ROTULO_COMISSAO[i.comissao_status]}{i.nota_fiscal ? ` · NF ${i.nota_fiscal}` : ""}{i.paga_em ? ` · paga em ${data(i.paga_em)}` : ""}</p> : null}
                </li>
              ))}
              {dados.indicacoes.length === 0 && <li className="py-3 text-sm text-slate-400">Sem indicações no período.</li>}
            </ul>
          </>
        )}
      </section>
    </div>
  )
}

function NovaIndicacao({ acesso, indicadores, onCriada }: { acesso: Acesso; indicadores: Indicador[]; onCriada: () => void }) {
  const [form, setForm] = useState({ indicador_id: acesso.indicador?.id || "", cliente_nome: "", cliente_id: "", regiao: "", linha: "TRAILER" as Linha, modelo: "", quantidade: "1", valor_final: "", oportunidade_id: "", observacao: "" })
  const [sugestoes, setSugestoes] = useState<ResultadoBusca | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")
  const [ok, setOk] = useState("")
  const mudar = (campo: keyof typeof form, valor: string) => setForm((f) => ({ ...f, [campo]: valor }))

  useEffect(() => {
    const termo = form.cliente_nome.trim()
    if (termo.length < 3 || form.cliente_id) return
    const controle = new AbortController()
    const id = window.setTimeout(() => { buscarNoCTI(termo, controle.signal).then(setSugestoes).catch(() => undefined) }, 300)
    return () => { window.clearTimeout(id); controle.abort() }
  }, [form.cliente_nome, form.cliente_id])

  const comissaoPrevista = (acesso.tabela_comissao[form.linha] || 0) * (Number(form.quantidade) || 0)

  async function enviar() {
    setEnviando(true); setErro(""); setOk("")
    try {
      await registrarIndicacao({
        indicador_id: form.indicador_id || undefined, cliente_id: form.cliente_id || undefined, cliente_nome: form.cliente_nome,
        regiao: form.regiao || undefined, linha: form.linha, modelo: form.modelo || undefined, quantidade: Number(form.quantidade),
        valor_final: Number(String(form.valor_final).replace(/\./g, "").replace(",", ".")) || 0, oportunidade_id: form.oportunidade_id || undefined, observacao: form.observacao || undefined,
      })
      setOk("Indicação registrada.")
      setForm((f) => ({ ...f, cliente_nome: "", cliente_id: "", regiao: "", modelo: "", quantidade: "1", valor_final: "", oportunidade_id: "", observacao: "" }))
      onCriada()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível registrar.")
    } finally {
      setEnviando(false)
    }
  }

  const empresas = form.cliente_id || form.cliente_nome.trim().length < 3 ? [] : sugestoes?.empresas || []
  return (
    <section aria-label="Nova indicação" className={caixa}>
      <h2 className="flex items-center gap-2 text-lg font-semibold"><Plus size={18} className="text-cyan-300"/> Nova indicação</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {!acesso.indicador && (
          <label className="text-xs text-slate-400">Indicador
            <select value={form.indicador_id} onChange={(e) => mudar("indicador_id", e.target.value)} className={campo}>
              <option value="">Escolha o indicador</option>
              {indicadores.filter((i) => i.ativo !== false).map((i) => <option key={i.id} value={i.id}>{i.nome}</option>)}
            </select>
          </label>
        )}
        <label className="relative text-xs text-slate-400">Cliente indicado
          <input value={form.cliente_nome} onChange={(e) => setForm((f) => ({ ...f, cliente_nome: e.target.value, cliente_id: "" }))} placeholder="Nome do cliente" className={campo}/>
          {form.cliente_id && <span className="text-[11px] text-emerald-300">Cliente do cadastro: a região vem da carteira se ficar em branco.</span>}
          {empresas.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full rounded-xl border border-[#24466f] bg-[#020817] text-sm">
              {empresas.slice(0, 5).map((e) => <li key={e.cliente_id}><button type="button" onClick={() => { setForm((f) => ({ ...f, cliente_nome: e.nome || "", cliente_id: e.cliente_id, regiao: f.regiao || e.cidade || "" })); setSugestoes(null) }} className="w-full px-3 py-2 text-left text-white hover:bg-[#0f2340]">{e.nome}{e.cidade ? ` · ${e.cidade}` : ""}</button></li>)}
            </ul>
          )}
        </label>
        <label className="text-xs text-slate-400">Região do cliente<input value={form.regiao} onChange={(e) => mudar("regiao", e.target.value)} placeholder="Ex.: Campinas, Grande SP, Vale" className={campo}/></label>
        <label className="text-xs text-slate-400">Linha
          <select value={form.linha} onChange={(e) => mudar("linha", e.target.value)} className={campo}>
            {LINHAS.map((l) => <option key={l} value={l}>{ROTULO_LINHA[l]} — {moeda(acesso.tabela_comissao[l])} por equipamento</option>)}
          </select>
        </label>
        <label className="text-xs text-slate-400">Máquina (modelo)<input value={form.modelo} onChange={(e) => mudar("modelo", e.target.value)} placeholder="Ex.: Vector HE19, Supra 850" className={campo}/></label>
        <label className="text-xs text-slate-400">Quantidade<input type="number" min={1} max={500} value={form.quantidade} onChange={(e) => mudar("quantidade", e.target.value)} className={campo}/></label>
        <label className="text-xs text-slate-400">Valor final (R$)<input inputMode="decimal" value={form.valor_final} onChange={(e) => mudar("valor_final", e.target.value)} placeholder="0,00" className={campo}/></label>
        <label className="text-xs text-slate-400">Oportunidade no CRM (opcional)<input value={form.oportunidade_id} onChange={(e) => mudar("oportunidade_id", e.target.value)} placeholder="Código da oportunidade" className={campo}/></label>
        <label className="text-xs text-slate-400 md:col-span-2 xl:col-span-1">Observação<input value={form.observacao} onChange={(e) => mudar("observacao", e.target.value)} maxLength={500} className={campo}/></label>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button type="button" disabled={enviando} onClick={() => void enviar()} className={`${botao} bg-cyan-500 text-slate-950`}>{enviando ? "Registrando..." : "Registrar indicação"}</button>
        <span className="text-xs text-slate-400">Comissão prevista se a venda for concluída: <b className="text-amber-200">{moeda(comissaoPrevista)}</b></span>
        {form.oportunidade_id && <span className="text-xs text-slate-500">Com a oportunidade vinculada, a venda é concluída sozinha quando o negócio for ganho.</span>}
      </div>
      {erro && <p role="alert" className="mt-2 text-sm text-red-300">{erro}</p>}
      {ok && <p role="status" className="mt-2 text-sm text-emerald-300">{ok}</p>}
    </section>
  )
}

function ListaIndicacoes({ acesso, periodo, versao, onAlterada }: { acesso: Acesso; periodo: Periodo; versao: number; onAlterada: () => void }) {
  const [itens, setItens] = useState<Indicacao[] | null>(null)
  const [erro, setErro] = useState("")
  const [filtro, setFiltro] = useState<"" | StatusIndicacao | "A_PAGAR">("")
  const [nota, setNota] = useState<Record<string, string>>({})
  const [ocupado, setOcupado] = useState("")

  useEffect(() => {
    let ativo = true
    buscarIndicacoes(periodo).then((r) => { if (ativo) { setItens(r); setErro("") } }).catch((e: unknown) => { if (ativo) setErro(e instanceof Error ? e.message : "Falha ao carregar.") })
    return () => { ativo = false }
  }, [periodo, versao])

  async function mudar(i: Indicacao, dados: Record<string, unknown>) {
    setOcupado(i.id); setErro("")
    try {
      await atualizarIndicacao(i.id, dados)
      onAlterada()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível atualizar.")
    } finally {
      setOcupado("")
    }
  }

  const podeMudarStatus = acesso.gestao || (acesso.interno && !acesso.indicador)
  const lista = (itens || []).filter((i) => !filtro || (filtro === "A_PAGAR" ? i.status === "VENDIDA" && i.comissao_status !== "PAGA" : i.status === filtro))
  return (
    <section aria-label="Indicações" className={caixa}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold"><Handshake size={18} className="text-cyan-300"/> {acesso.indicador ? "Minhas indicações" : "Indicações"}</h2>
        <select aria-label="Filtrar indicações" value={filtro} onChange={(e) => setFiltro(e.target.value as typeof filtro)} className={campoBase}>
          <option value="">Todas</option>
          {(Object.keys(ROTULO_STATUS) as StatusIndicacao[]).map((s) => <option key={s} value={s}>{ROTULO_STATUS[s]}</option>)}
          {(acesso.gestao || acesso.indicador) && <option value="A_PAGAR">Comissão pendente</option>}
        </select>
      </div>
      {erro && <p role="alert" className="mt-2 text-sm text-red-300">{erro}</p>}
      {!itens && !erro && <div className="grid min-h-24 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
      <ul className="mt-3 divide-y divide-[#13203f]">
        {lista.map((i) => (
          <li key={i.id} className="flex flex-col gap-2 py-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <p className="flex flex-wrap items-center gap-2"><strong>{i.cliente_nome}</strong><span className={`rounded-full border px-2 py-0.5 text-[11px] ${COR_STATUS[i.status]}`}>{ROTULO_STATUS[i.status]}</span>{i.comissao_status && <span className="rounded-full border border-amber-800 px-2 py-0.5 text-[11px] text-amber-200">{ROTULO_COMISSAO[i.comissao_status]}{i.nota_fiscal ? ` · NF ${i.nota_fiscal}` : ""}</span>}</p>
              <p className="text-xs text-slate-400">{[!acesso.indicador && `Indicador: ${i.indicador_nome}`, i.regiao, `${i.quantidade}× ${ROTULO_LINHA[i.linha]}${i.modelo ? ` ${i.modelo}` : ""}`, moeda(i.valor_final), `indicada em ${data(i.data_indicacao)}`, i.data_venda && `vendida em ${data(i.data_venda)}`, i.comissao_valor ? `comissão ${moeda(i.comissao_valor)}` : null].filter(Boolean).join(" · ")}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {podeMudarStatus && i.status !== "VENDIDA" && i.status !== "PERDIDA" && (
                <>
                  {i.status === "INDICADA" && <button type="button" disabled={ocupado === i.id} onClick={() => void mudar(i, { status: "EM_NEGOCIACAO" })} className="min-h-9 rounded-xl border border-cyan-800 px-3 text-xs text-cyan-200">Em negociação</button>}
                  <button type="button" disabled={ocupado === i.id} onClick={() => void mudar(i, { status: "VENDIDA" })} className="min-h-9 rounded-xl border border-emerald-800 px-3 text-xs text-emerald-200">Venda concluída</button>
                  <button type="button" disabled={ocupado === i.id} onClick={() => void mudar(i, { status: "PERDIDA" })} className="min-h-9 rounded-xl border border-red-900 px-3 text-xs text-red-200">Perdida</button>
                </>
              )}
              {acesso.gestao && i.status === "VENDIDA" && i.comissao_status === "A_PAGAR" && (
                <span className="flex items-center gap-1">
                  <input aria-label={`Nota fiscal de ${i.cliente_nome}`} value={nota[i.id] || ""} onChange={(e) => setNota((n) => ({ ...n, [i.id]: e.target.value }))} placeholder="Nº da NF" className="min-h-9 w-28 rounded-xl border border-[#24466f] bg-[#020817] px-2 text-xs"/>
                  <button type="button" disabled={ocupado === i.id || !nota[i.id]} onClick={() => void mudar(i, { comissao_status: "NF_RECEBIDA", nota_fiscal: nota[i.id] })} className="min-h-9 rounded-xl border border-amber-800 px-3 text-xs text-amber-200 disabled:opacity-40">NF recebida</button>
                </span>
              )}
              {acesso.gestao && i.comissao_status === "NF_RECEBIDA" && <button type="button" disabled={ocupado === i.id} onClick={() => void mudar(i, { comissao_status: "PAGA" })} className="min-h-9 rounded-xl bg-emerald-600 px-3 text-xs font-bold text-white">Marcar comissão paga</button>}
            </div>
          </li>
        ))}
        {itens && lista.length === 0 && <li className="py-3 text-sm text-slate-400">Nenhuma indicação para este filtro.</li>}
      </ul>
    </section>
  )
}

function CadastroIndicadores({ indicadores, onSalvo, onExtrato }: { indicadores: Indicador[]; onSalvo: () => void; onExtrato: (id: string) => void }) {
  const vazio = { nome: "", documento: "", telefone: "", email: "", regiao: "", usuario_id: "", dados_pagamento: "", ativo: true }
  const [form, setForm] = useState(vazio)
  const [editando, setEditando] = useState<string | null>(null)
  const [usuarios, setUsuarios] = useState<UsuarioCTI[]>([])
  const [erro, setErro] = useState("")
  useEffect(() => { listarUsuarios().then((u) => setUsuarios(u.filter((x) => String(x.tipo_usuario || "").toUpperCase().startsWith("INDICADOR")))).catch(() => setUsuarios([])) }, [])

  async function salvar() {
    setErro("")
    try {
      await salvarIndicador({ ...form, documento: form.documento || null, usuario_id: form.usuario_id || null }, editando || undefined)
      setForm(vazio); setEditando(null); onSalvo()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar.")
    }
  }

  return (
    <section aria-label="Cadastro de indicadores" className={caixa}>
      <h2 className="flex items-center gap-2 text-lg font-semibold"><Users size={18} className="text-cyan-300"/> Indicadores</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <label className="text-xs text-slate-400">Nome<input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} className={campo}/></label>
        <label className="text-xs text-slate-400">CPF ou CNPJ (emite a NF)<input value={form.documento} onChange={(e) => setForm({ ...form, documento: e.target.value })} className={campo}/></label>
        <label className="text-xs text-slate-400">Telefone<input value={form.telefone} onChange={(e) => setForm({ ...form, telefone: e.target.value })} className={campo}/></label>
        <label className="text-xs text-slate-400">E-mail<input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={campo}/></label>
        <label className="text-xs text-slate-400">Região de atuação<input value={form.regiao} onChange={(e) => setForm({ ...form, regiao: e.target.value })} className={campo}/></label>
        <label className="text-xs text-slate-400">Dados para pagamento<input value={form.dados_pagamento} onChange={(e) => setForm({ ...form, dados_pagamento: e.target.value })} placeholder="Banco, agência, conta ou PIX" className={campo}/></label>
        <label className="text-xs text-slate-400">Acesso ao CTI (usuário indicador)
          <select value={form.usuario_id} onChange={(e) => setForm({ ...form, usuario_id: e.target.value })} className={campo}>
            <option value="">Sem acesso</option>
            {usuarios.map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 text-xs text-slate-400"><input type="checkbox" checked={form.ativo} onChange={(e) => setForm({ ...form, ativo: e.target.checked })}/> Ativo</label>
      </div>
      <div className="mt-3 flex gap-2">
        <button type="button" onClick={() => void salvar()} className={`${botao} bg-cyan-500 text-slate-950`}>{editando ? "Salvar alterações" : "Cadastrar indicador"}</button>
        {editando && <button type="button" onClick={() => { setEditando(null); setForm(vazio) }} className={`${botao} border border-[#24466f]`}>Cancelar</button>}
      </div>
      {erro && <p role="alert" className="mt-2 text-sm text-red-300">{erro}</p>}
      <ul className="mt-4 divide-y divide-[#13203f]">
        {indicadores.map((i) => (
          <li key={i.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
            <span><strong>{i.nome}</strong> <span className="text-xs text-slate-400">{[i.documento, i.regiao, i.telefone, i.ativo === false && "inativo", i.usuario_id && "com acesso ao CTI"].filter(Boolean).join(" · ")}</span></span>
            <span className="flex gap-2">
              <button type="button" onClick={() => onExtrato(i.id)} className="min-h-9 rounded-xl border border-[#24466f] px-3 text-xs"><FileText size={14} className="mr-1 inline"/>Extrato</button>
              <button type="button" onClick={() => { setEditando(i.id); setForm({ nome: i.nome, documento: i.documento || "", telefone: i.telefone || "", email: i.email || "", regiao: i.regiao || "", usuario_id: i.usuario_id || "", dados_pagamento: i.dados_pagamento || "", ativo: i.ativo !== false }) }} className="min-h-9 rounded-xl border border-[#24466f] px-3 text-xs">Editar</button>
            </span>
          </li>
        ))}
        {indicadores.length === 0 && <li className="py-2 text-sm text-slate-400">Cadastre o primeiro indicador para começar.</li>}
      </ul>
    </section>
  )
}

function PainelGestao({ periodo, versao, onExtrato }: { periodo: Periodo; versao: number; onExtrato: (id: string) => void }) {
  const [dados, setDados] = useState<Painel | null>(null)
  const [erro, setErro] = useState("")
  useEffect(() => {
    let ativo = true
    buscarPainel(periodo).then((d) => { if (ativo) { setDados(d); setErro("") } }).catch((e: unknown) => { if (ativo) setErro(e instanceof Error ? e.message : "Falha ao carregar o painel.") })
    return () => { ativo = false }
  }, [periodo, versao])
  if (erro) return <p role="alert" className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</p>
  if (!dados) return <div className="grid min-h-32 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>
  const t = dados.total
  const peso = dados.peso_nas_vendas
  return (
    <>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Cartao titulo="Indicações" valor={numero(t.indicacoes)} detalhe={`${numero(t.em_aberto)} em aberto (${moeda(t.valor_em_aberto)})`}/>
        <Cartao titulo="Vendas por indicação" valor={numero(t.vendidas)} detalhe={`${numero(t.equipamentos_vendidos)} equipamentos · conversão ${pct(t.conversao)}`}/>
        <Cartao titulo="Valor vendido por indicação" valor={moeda(t.valor_vendido)} detalhe={peso.participacao_valor !== null ? `${pct(peso.participacao_valor)} do vendido pela Viena (${moeda(peso.valor_vendido_viena)})` : "Sem total da Viena no período"} destaque="text-cyan-300"/>
        <Cartao titulo="Peso em equipamentos" valor={pct(peso.participacao_equipamentos)} detalhe={peso.equipamentos_vendidos_viena ? `${numero(t.equipamentos_vendidos)} de ${numero(peso.equipamentos_vendidos_viena)} vendidos` : "Sem base de vendas no período"}/>
        <Cartao titulo="Comissão total" valor={moeda(t.comissao_total)} detalhe="vendas concluídas no período"/>
        <Cartao titulo="A pagar (aguardando NF)" valor={moeda(t.comissao_a_pagar)} destaque="text-amber-300"/>
        <Cartao titulo="NF recebida (pagar)" valor={moeda(t.comissao_nf_recebida)} destaque="text-amber-200"/>
        <Cartao titulo="Comissão paga" valor={moeda(t.comissao_paga)} destaque="text-emerald-300"/>
      </div>
      <TabelaAgregado titulo="Resultado por indicador" linhas={dados.por_indicador} rotulo={(l) => l.nome} onAbrir={(l) => onExtrato(l.indicador_id)}/>
      <TabelaAgregado titulo="Resultado por região" linhas={dados.por_regiao} rotulo={(l) => l.regiao} extra={(l) => pct(l.participacao_no_indicado)}/>
      <TabelaAgregado titulo="Resultado por linha" linhas={dados.por_linha} rotulo={(l) => `${ROTULO_LINHA[l.linha]} (${moeda(l.comissao_por_equipamento)}/equip.)`}/>
    </>
  )
}

export default function IndicadoresPage() {
  const [acesso, setAcesso] = useState<Acesso | null>(null)
  const [erro, setErro] = useState("")
  const [aba, setAba] = useState<"painel" | "indicacoes" | "indicadores">("painel")
  const [periodo, setPeriodo] = useState<Periodo>({ ano: new Date().getFullYear() })
  const [indicadores, setIndicadores] = useState<Indicador[]>([])
  const [versao, setVersao] = useState(0)
  const [extrato, setExtrato] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    buscarAcesso().then((a) => { if (ativo) { setAcesso(a); if (!a.gestao) setAba("indicacoes") } }).catch((e: unknown) => { if (ativo) setErro(e instanceof Error ? e.message : "Sem acesso ao módulo.") })
    return () => { ativo = false }
  }, [])
  useEffect(() => {
    if (!acesso) return
    let ativo = true
    buscarIndicadores().then((l) => { if (ativo) setIndicadores(l) }).catch(() => { if (ativo) setIndicadores([]) })
    return () => { ativo = false }
  }, [acesso, versao])

  const recarregar = () => setVersao((v) => v + 1)
  const abas = useMemo(() => acesso?.gestao ? [["painel", "Painel e relatórios"], ["indicacoes", "Indicações"], ["indicadores", "Indicadores"]] as const : [["indicacoes", acesso?.indicador ? "Minhas indicações" : "Indicações"]] as const, [acesso])

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar/>
      <section className="min-w-0 flex-1">
        <Topbar/>
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">CRM</p>
              <h1 className="mt-2 flex items-center gap-2 text-3xl font-bold sm:text-4xl"><BadgeDollarSign className="text-cyan-300"/> Indicadores e comissões</h1>
              <p className="mt-2 max-w-3xl text-gray-400">Quem indicou, para qual cliente e região, qual máquina, quantidade e valor final. Venda concluída gera a comissão por equipamento: Trailer {moeda(acesso?.tabela_comissao.TRAILER ?? 1400)}, Diesel Truck {moeda(acesso?.tabela_comissao["DIESEL TRUCK"] ?? 900)} e Direct Drive {moeda(acesso?.tabela_comissao["DIRECT DRIVE"] ?? 400)}. O pagamento é feito com a nota fiscal do indicador.</p>
            </div>
            <Seletor periodo={periodo} onMudar={setPeriodo}/>
          </header>
          {erro && <p role="alert" className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</p>}
          {!acesso && !erro && <div className="grid min-h-40 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
          {acesso && (
            <>
              {abas.length > 1 && (
                <div role="tablist" aria-label="Seções" className="flex gap-2 overflow-x-auto">
                  {abas.map(([codigo, rotulo]) => <button key={codigo} type="button" role="tab" aria-selected={aba === codigo} onClick={() => setAba(codigo)} className={`shrink-0 rounded-full border px-4 py-2 text-sm font-semibold ${aba === codigo ? "border-cyan-500 bg-cyan-950/60 text-cyan-100" : "border-[#24466f] text-slate-400"}`}>{rotulo}</button>)}
                </div>
              )}
              {acesso.indicador && <button type="button" onClick={() => setExtrato(acesso.indicador!.id)} className={`${botao} border border-[#24466f]`}><FileText size={16}/>Meu extrato de comissões</button>}
              {aba === "painel" && acesso.gestao && <PainelGestao periodo={periodo} versao={versao} onExtrato={setExtrato}/>}
              {aba === "indicacoes" && (
                <>
                  <NovaIndicacao acesso={acesso} indicadores={indicadores} onCriada={recarregar}/>
                  <ListaIndicacoes acesso={acesso} periodo={periodo} versao={versao} onAlterada={recarregar}/>
                </>
              )}
              {aba === "indicadores" && acesso.gestao && <CadastroIndicadores indicadores={indicadores} onSalvo={recarregar} onExtrato={setExtrato}/>}
            </>
          )}
        </div>
      </section>
      {extrato && <ExtratoModal indicadorId={extrato} periodo={periodo} onFechar={() => setExtrato(null)}/>}
    </main>
  )
}
