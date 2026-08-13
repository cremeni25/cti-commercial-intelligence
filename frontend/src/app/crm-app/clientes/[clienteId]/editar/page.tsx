"use client"

import Link from "next/link"
import { FormEvent, useEffect, useState } from "react"
import { ArrowLeft, Building2, Loader2, Save } from "lucide-react"
import { useParams, useRouter } from "next/navigation"

type Registro = Record<string, unknown>

const categorias = [
  ["TRANSPORTADORA", "Transportadora"],
  ["PRODUTOR", "Produtor"],
  ["EMBARCADOR", "Embarcador"],
  ["LOCADORA", "Locadora"],
  ["IMPLEMENTADORA", "Implementadora"],
  ["DISTRIBUIDORA", "Distribuidora"],
] as const

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function valor(dados: FormData, campo: string) { return String(dados.get(campo) || "").trim() }

export default function EditarClientePage() {
  const params = useParams<{ clienteId: string }>()
  const router = useRouter()
  const clienteId = decodeURIComponent(String(params.clienteId || ""))
  const [cliente, setCliente] = useState<Registro | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  useEffect(() => {
    let ativo = true
    fetch(`/api/crm-proxy/crm-app/clientes/${encodeURIComponent(clienteId)}`, { cache: "no-store" })
      .then(async (resposta) => {
        const payload = await resposta.json().catch(() => ({}))
        if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Não foi possível carregar o cliente (${resposta.status}).`)
        if (ativo) setCliente(payload as Registro)
      })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o cliente.") })
      .finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [clienteId])

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const formulario = evento.currentTarget
    setSalvando(true); setErro(""); setSucesso("")
    const dados = new FormData(formulario)
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
    if (!payload.nome || !payload.cidade || !payload.estado || !payload.categoria) {
      setErro("Preencha razão social, cidade, UF e categoria."); setSalvando(false); return
    }
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-app/clientes/${encodeURIComponent(clienteId)}`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      })
      const retorno = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(retorno.detail) || `Não foi possível atualizar o cliente (${resposta.status}).`)
      const atualizado = retorno.cliente && typeof retorno.cliente === "object" ? retorno.cliente as Registro : payload
      setCliente(atualizado)
      setSucesso("Cadastro atualizado e disponível em toda a jornada comercial.")
      window.setTimeout(() => router.push(`/crm-app/clientes/${encodeURIComponent(texto(atualizado.id) || clienteId)}?nome=${encodeURIComponent(payload.nome)}`), 700)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao atualizar cliente.") }
    finally { setSalvando(false) }
  }

  if (carregando) return <main className="grid min-h-[100dvh] place-items-center bg-[#020817] text-cyan-300"><Loader2 className="animate-spin" /></main>

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6"><div className="mx-auto max-w-4xl">
    <header className="mb-5 flex items-center gap-3"><Link href={`/crm-app/clientes/${encodeURIComponent(clienteId)}`} className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Editar cliente</h1><p className="text-sm text-slate-400">Atualize o cadastro mestre sem sair do aplicativo</p></div></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{sucesso}</div>}
    {cliente && <form onSubmit={salvar} className="space-y-5 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6">
      <div className="flex items-center gap-3"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2 size={22}/></span><div><h2 className="font-bold">Dados cadastrais</h2><p className="text-sm text-slate-400">Dados fiscais, endereço e contatos do cliente.</p></div></div>
      <section className="grid gap-4 sm:grid-cols-2"><Campo label="Nome / razão social" name="nome" valor={texto(cliente.nome || cliente.razao_social || cliente.nome_fantasia)} required/><Campo label="CNPJ" name="cnpj" valor={texto(cliente.cnpj)} inputMode="numeric"/><Campo label="Inscrição estadual" name="inscricao_estadual" valor={texto(cliente.inscricao_estadual)}/><label className="text-sm text-slate-300">Categoria<select name="categoria" defaultValue={texto(cliente.categoria || cliente.segmento) || "TRANSPORTADORA"} required className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4">{categorias.map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label></section>
      <section><h3 className="mb-3 font-semibold text-slate-200">Endereço</h3><div className="grid gap-4 sm:grid-cols-2"><Campo label="Endereço" name="endereco" valor={texto(cliente.endereco)}/><Campo label="Número" name="numero" valor={texto(cliente.numero)}/><Campo label="Complemento" name="complemento" valor={texto(cliente.complemento)}/><Campo label="Bairro" name="bairro" valor={texto(cliente.bairro)}/><Campo label="Cidade" name="cidade" valor={texto(cliente.cidade || cliente.municipio)} required/><Campo label="UF" name="estado" valor={texto(cliente.estado || cliente.uf)} maxLength={2} required/><Campo label="CEP" name="cep" valor={texto(cliente.cep)} inputMode="numeric"/><Campo label="DDD" name="ddd" valor={texto(cliente.ddd)} inputMode="numeric"/><Campo label="Sub-região" name="sub_regiao" valor={texto(cliente.sub_regiao || cliente.subRegiao)}/></div></section>
      <section><h3 className="mb-3 font-semibold text-slate-200">Contato comercial e fiscal</h3><div className="grid gap-4 sm:grid-cols-2"><Campo label="Contato" name="contato" valor={texto(cliente.contato)}/><Campo label="Fone" name="fone" valor={texto(cliente.fone || cliente.telefone)} inputMode="tel"/><Campo label="E-mail" name="email" valor={texto(cliente.email)} type="email"/><Campo label="E-mail para XML" name="email_xml" valor={texto(cliente.email_xml)} type="email"/></div></section>
      <button disabled={salvando} className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-50">{salvando ? <Loader2 className="animate-spin" size={18}/> : <Save size={18}/>}Salvar alterações</button>
    </form>}
  </div></main>
}

function Campo({ label, name, valor: valorInicial, required = false, maxLength, type = "text", inputMode }: { label:string; name:string; valor:string; required?:boolean; maxLength?:number; type?:string; inputMode?:"numeric"|"tel" }) {
  return <label className="text-sm text-slate-300">{label}<input name={name} type={type} required={required} maxLength={maxLength} inputMode={inputMode} defaultValue={valorInicial} className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4"/></label>
}
