"use client"

import Link from "next/link"
import { FormEvent, useState } from "react"
import { ArrowLeft, Building2, Loader2, Save } from "lucide-react"

const categorias = [
  ["TRANSPORTADORA", "Transportadora"],
  ["PRODUTOR", "Produtor"],
  ["EMBARCADOR", "Embarcador"],
  ["LOCADORA", "Locadora"],
  ["IMPLEMENTADORA", "Implementadora"],
  ["DISTRIBUIDORA", "Distribuidora"],
] as const

function valor(dados: FormData, campo: string) {
  return String(dados.get(campo) || "").trim()
}

export default function NovoClientePage() {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true); setErro(""); setSucesso("")
    const dados = new FormData(evento.currentTarget)
    const payload = {
      nome: valor(dados, "nome"),
      cnpj: valor(dados, "cnpj") || null,
      inscricao_estadual: valor(dados, "inscricao_estadual") || null,
      endereco: valor(dados, "endereco") || null,
      numero: valor(dados, "numero") || null,
      complemento: valor(dados, "complemento") || null,
      bairro: valor(dados, "bairro") || null,
      cidade: valor(dados, "cidade") || null,
      estado: valor(dados, "estado").toUpperCase() || null,
      cep: valor(dados, "cep") || null,
      contato: valor(dados, "contato") || null,
      fone: valor(dados, "fone") || null,
      email: valor(dados, "email") || null,
      email_xml: valor(dados, "email_xml") || null,
      categoria: valor(dados, "categoria") || "TRANSPORTADORA",
      ddd: valor(dados, "ddd") || null,
      sub_regiao: valor(dados, "sub_regiao") || null,
    }

    if (!payload.nome || !payload.cnpj || !payload.cidade || !payload.estado || !payload.categoria) {
      setErro("Preencha razão social, CNPJ, cidade, UF e categoria.")
      setSalvando(false)
      return
    }

    try {
      const resposta = await fetch("/api/crm-proxy/crm-app/clientes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const retorno = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(retorno.detail || `Não foi possível cadastrar o cliente (${resposta.status}).`))
      evento.currentTarget.reset()
      setSucesso("Cliente cadastrado com sucesso e disponível em toda a jornada comercial.")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao cadastrar cliente.")
    } finally {
      setSalvando(false)
    }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-4xl">
      <header className="mb-5 flex items-center gap-3">
        <Link href="/crm-app/clientes" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
        <div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Novo cliente</h1><p className="text-sm text-slate-400">Cadastro mestre para oportunidades, atividades, propostas, pedidos e faturamento</p></div>
      </header>

      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{sucesso}</div>}

      <form onSubmit={salvar} className="space-y-5 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6">
        <div className="flex items-center gap-3"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2 size={22}/></span><div><h2 className="font-bold">Dados cadastrais</h2><p className="text-sm text-slate-400">Identificação fiscal, endereço e contatos do cliente.</p></div></div>

        <section className="grid gap-4 sm:grid-cols-2">
          <Campo label="Nome / razão social" name="nome" required />
          <Campo label="CNPJ" name="cnpj" inputMode="numeric" required />
          <Campo label="Inscrição estadual" name="inscricao_estadual" />
          <label className="text-sm text-slate-300">Categoria<select name="categoria" defaultValue="TRANSPORTADORA" required className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4">{categorias.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select></label>
        </section>

        <section><h3 className="mb-3 font-semibold text-slate-200">Endereço</h3><div className="grid gap-4 sm:grid-cols-2">
          <Campo label="Endereço" name="endereco" />
          <Campo label="Número" name="numero" />
          <Campo label="Complemento" name="complemento" />
          <Campo label="Bairro" name="bairro" />
          <Campo label="Cidade" name="cidade" required />
          <Campo label="UF" name="estado" maxLength={2} required />
          <Campo label="CEP" name="cep" inputMode="numeric" />
          <Campo label="DDD" name="ddd" inputMode="numeric" />
          <Campo label="Sub-região" name="sub_regiao" />
        </div></section>

        <section><h3 className="mb-3 font-semibold text-slate-200">Contato comercial e fiscal</h3><div className="grid gap-4 sm:grid-cols-2">
          <Campo label="Contato" name="contato" />
          <Campo label="Fone" name="fone" inputMode="tel" />
          <Campo label="E-mail" name="email" type="email" />
          <Campo label="E-mail para envio de XML" name="email_xml" type="email" />
        </div></section>

        <button disabled={salvando} className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-50">{salvando ? <Loader2 className="animate-spin" size={18}/> : <Save size={18}/>}Salvar cliente</button>
      </form>
    </div>
  </main>
}

function Campo({ label, name, required = false, maxLength, type = "text", inputMode }: { label: string; name: string; required?: boolean; maxLength?: number; type?: string; inputMode?: "numeric" | "tel" }) {
  return <label className="text-sm text-slate-300">{label}<input name={name} type={type} required={required} maxLength={maxLength} inputMode={inputMode} className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4"/></label>
}
