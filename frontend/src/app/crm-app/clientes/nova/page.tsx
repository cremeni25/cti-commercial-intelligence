"use client"

import Link from "next/link"
import { FormEvent, useState } from "react"
import { ArrowLeft, Building2, Loader2, Save } from "lucide-react"

export default function NovoClientePage() {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true); setErro(""); setSucesso("")
    const dados = new FormData(evento.currentTarget)
    const payload = {
      nome: String(dados.get("nome") || "").trim(),
      cidade: String(dados.get("cidade") || "").trim() || null,
      estado: String(dados.get("estado") || "").trim().toUpperCase() || null,
      segmento: String(dados.get("segmento") || "TRANSPORTADOR"),
      ddd: String(dados.get("ddd") || "").trim() || null,
      sub_regiao: String(dados.get("sub_regiao") || "").trim() || null,
    }
    if (!payload.nome) { setErro("Informe o nome do cliente."); setSalvando(false); return }
    try {
      const resposta = await fetch("/api/crm-proxy/crm-app/clientes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      const retorno = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(retorno.detail || `Não foi possível cadastrar o cliente (${resposta.status}).`))
      evento.currentTarget.reset()
      setSucesso("Cliente cadastrado com sucesso e disponível para oportunidades e atividades.")
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao cadastrar cliente.") }
    finally { setSalvando(false) }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-3xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/clientes" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Novo cliente</h1><p className="text-sm text-slate-400">Cadastro comercial para uso em toda a jornada do CRM</p></div></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{sucesso}</div>}
    <form onSubmit={salvar} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6">
      <div className="mb-5 flex items-center gap-3"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2 size={22}/></span><div><h2 className="font-bold">Identificação do cliente</h2><p className="text-sm text-slate-400">Os dados serão reutilizados em oportunidades, atividades, propostas e pedidos.</p></div></div>
      <div className="grid gap-4 sm:grid-cols-2"><Campo label="Nome / razão social" name="nome" required/><Campo label="Município" name="cidade"/><Campo label="UF" name="estado" maxLength={2}/><Campo label="DDD" name="ddd"/><Campo label="Sub-região" name="sub_regiao"/><label className="text-sm text-slate-300">Segmento<select name="segmento" defaultValue="TRANSPORTADOR" className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4"><option value="TRANSPORTADOR">Transportador</option><option value="DISTRIBUIDOR">Distribuidor</option><option value="VAREJO">Varejo</option><option value="INDUSTRIA">Indústria</option><option value="OUTRO">Outro</option></select></label></div>
      <button disabled={salvando} className="mt-6 flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-50">{salvando ? <Loader2 className="animate-spin" size={18}/> : <Save size={18}/>}Salvar cliente</button>
    </form>
  </div></main>
}

function Campo({ label, name, required = false, maxLength }: { label: string; name: string; required?: boolean; maxLength?: number }) { return <label className="text-sm text-slate-300">{label}<input name={name} required={required} maxLength={maxLength} className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4"/></label> }
