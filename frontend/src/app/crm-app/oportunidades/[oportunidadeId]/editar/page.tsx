"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, Loader2, Plus, Save, Search } from "lucide-react"
import { lerContextoOportunidade, montarDescricaoComContexto } from "@/lib/crm-opportunity"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
function texto(valor: unknown) { return String(valor || "").trim() }
function numero(valor: unknown) { const n = Number(valor || 0); return Number.isFinite(n) ? n : 0 }
function nomeCliente(item: Registro) { return texto(item.razao_social || item.nome || item.nome_fantasia || item.empresa || item.cliente) }
function cnpjCliente(item: Registro) { return texto(item.cnpj).replace(/\D/g, "") }
function formatarCnpj(valor: string) { const v = valor.replace(/\D/g, "").slice(0, 14); return v.length === 14 ? v.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5") : v }

export default function EditarOportunidade() {
  const params = useParams<{ oportunidadeId: string }>()
  const searchParams = useSearchParams(); const router = useRouter(); const id = String(params.oportunidadeId || "")
  const origemParam = searchParams.get("origem") || "oportunidades"
  const origem = origemParam === "pipeline" ? "pipeline" : origemParam === "clientes" ? "clientes" : "oportunidades"
  const voltar = origem === "clientes" ? `/crm-app/historico/${id}?origem=clientes` : `/crm-app/${origem}`
  const [dados, setDados] = useState<Registro>({}); const [grupo, setGrupo] = useState<Registro>({}); const [estabelecimentos, setEstabelecimentos] = useState<Registro[]>([])
  const [busca, setBusca] = useState(""); const [novoCnpj, setNovoCnpj] = useState(""); const [adicionando, setAdicionando] = useState(false)
  const [carregando, setCarregando] = useState(true); const [salvando, setSalvando] = useState(false); const [erro, setErro] = useState(""); const [sucesso, setSucesso] = useState("")
  const contexto = useMemo(() => lerContextoOportunidade(dados), [dados])

  async function obter() { const r = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}`, { cache: "no-store" }); const p = await r.json().catch(() => ({})); if (!r.ok) throw new Error(texto((p as Registro).detail) || `Falha ${r.status}`); return (Array.isArray(p) ? p[0] || {} : p) as Registro }
  async function obterGrupo() { const r = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}/estabelecimentos`, { cache: "no-store" }); const p = await r.json().catch(() => ({})) as Registro; if (!r.ok) throw new Error(texto(p.detail) || `Falha ${r.status}`); setGrupo((p.grupo || {}) as Registro); setEstabelecimentos(Array.isArray(p.estabelecimentos) ? p.estabelecimentos as Registro[] : []) }

  useEffect(() => { void Promise.all([obter(), obterGrupo()]).then(([o]) => setDados(o)).catch(f => setErro(f instanceof Error ? f.message : "Não foi possível carregar a negociação.")).finally(() => setCarregando(false)) }, [id])

  async function adicionarCnpj() {
    const cnpj = novoCnpj.replace(/\D/g, ""); if (cnpj.length !== 14) { setErro("Informe um CNPJ com 14 dígitos."); return }
    setAdicionando(true); setErro(""); setSucesso("")
    try { const r = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}/estabelecimentos`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cnpj }) }); const p = await r.json().catch(() => ({})) as Registro; if (!r.ok) throw new Error(texto(p.detail) || `Falha ${r.status}`); await obterGrupo(); setNovoCnpj(""); setSucesso("CNPJ validado e adicionado ao grupo. Agora selecione-o para esta negociação e salve.") } catch (f) { setErro(f instanceof Error ? f.message : "Não foi possível adicionar o CNPJ.") } finally { setAdicionando(false) }
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setSalvando(true); setErro(""); setSucesso(""); const form = new FormData(evento.currentTarget)
    const equipamento = texto(form.get("equipamento")); const municipio = texto(form.get("municipio")); const estado = texto(form.get("estado")).toUpperCase(); const descricaoBase = texto(form.get("descricao")); const clienteId = texto(form.get("cliente_id"))
    const descricao = montarDescricaoComContexto(descricaoBase, { linhas: contexto.linhas, equipamentos: equipamento ? equipamento.split(",").map(i => i.trim()).filter(Boolean) : contexto.equipamentos, quantidade: contexto.quantidade, municipio: municipio || contexto.municipio, uf: estado || contexto.uf, ddd: contexto.ddd, subRegiao: contexto.subRegiao })
    const payload: Registro = { titulo: texto(form.get("titulo")), descricao, status: texto(form.get("status")), valor_estimado: numero(form.get("valor_estimado")), probabilidade: numero(form.get("probabilidade")), data_fechamento_prevista: texto(form.get("data_fechamento_prevista")) || null, equipamento: equipamento || null, municipio: municipio || null, estado: estado || null }
    try { if (clienteId && clienteId !== texto(dados.cliente_id)) { const t = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}/estabelecimento`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cliente_id: clienteId, motivo: "Estabelecimento/CNPJ selecionado para esta negociação." }) }); const d = await t.json().catch(() => ({})) as Registro; if (!t.ok) throw new Error(texto(d.detail) || `Falha ${t.status}`) }
      const r = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); const p = await r.json().catch(() => ({})) as Registro; if (!r.ok) throw new Error(texto(p.detail) || `Falha ${r.status}`); setDados(await obter()); await obterGrupo(); setSucesso("Negociação atualizada. Histórico e documentos já emitidos permanecem preservados.")
    } catch (f) { setErro(f instanceof Error ? f.message : "Não foi possível atualizar a negociação.") } finally { setSalvando(false) }
  }

  const filtrados = estabelecimentos.filter(item => { const q = busca.toLowerCase().replace(/\D/g, ""); const qt = busca.toLowerCase(); return !busca || nomeCliente(item).toLowerCase().includes(qt) || cnpjCliente(item).includes(q) || texto(item.cidade).toLowerCase().includes(qt) })
  const equipamentoExibido = texto(dados.equipamento) || contexto.equipamentos.join(", "); const municipioExibido = texto(dados.municipio) || contexto.municipio; const estadoExibido = texto(dados.estado || dados.uf) || contexto.uf

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6"><div className="mx-auto max-w-3xl">
    <header className="mb-5 flex items-center gap-3"><button onClick={() => router.push(voltar)} className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></button><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Editar negociação</h1><p className="text-sm text-slate-400">Dados comerciais e CNPJ desta negociação</p></div></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}{sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}
    {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : <form onSubmit={salvar} className="grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:grid-cols-2">
      <section className="space-y-3 sm:col-span-2"><div><span className="text-xs uppercase tracking-wider text-slate-500">Cliente / grupo econômico</span><p className="font-semibold">{nomeCliente(grupo) || nomeCliente(dados) || "Cliente atual"}</p></div>
        <label className="block"><span className="mb-2 block text-sm text-slate-300">CNPJ desta negociação</span><select name="cliente_id" defaultValue={texto(dados.cliente_id)} className="min-h-12 w-full rounded-2xl border border-cyan-800 bg-[#020817] px-4 py-3" required>{filtrados.map(item => { const cid=texto(item.id); return <option key={cid} value={cid}>{nomeCliente(item)}{cnpjCliente(item) ? ` — ${formatarCnpj(cnpjCliente(item))}` : ""}{texto(item.cidade) ? ` — ${texto(item.cidade)}` : ""}</option> })}</select></label>
        <div className="relative"><Search className="absolute left-3 top-3.5 text-slate-500" size={18}/><input value={busca} onChange={e => setBusca(e.target.value)} placeholder="Pesquisar CNPJ, razão social ou cidade" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] pl-10 pr-4"/></div>
        <div className="rounded-2xl border border-[#24466f] bg-[#020817]/60 p-4"><p className="mb-2 text-sm font-semibold">Adicionar CNPJ ao grupo</p><div className="flex flex-col gap-2 sm:flex-row"><input value={novoCnpj} onChange={e => setNovoCnpj(e.target.value)} inputMode="numeric" placeholder="Digite o CNPJ" className="h-12 flex-1 rounded-xl border border-[#24466f] bg-[#020817] px-4"/><button type="button" onClick={() => void adicionarCnpj()} disabled={adicionando} className="flex h-12 items-center justify-center gap-2 rounded-xl border border-cyan-700 px-4 font-semibold text-cyan-300 disabled:opacity-60">{adicionando ? <Loader2 className="animate-spin" size={18}/> : <Plus size={18}/>}Validar e adicionar</button></div></div>
        <p className="text-xs text-slate-500">Somente CNPJs vinculados a este grupo aparecem aqui. A troca vale para esta negociação; histórico e documentos já emitidos não são reescritos.</p></section>
      <Campo name="titulo" label="Título" valor={texto(dados.titulo)} required/><label><span className="mb-2 block text-sm text-slate-300">Etapa</span><select name="status" defaultValue={texto(dados.status) || "OPORTUNIDADE"} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option>OPORTUNIDADE</option><option>ATIVIDADES</option><option>PROPOSTA</option><option>NEGOCIACAO</option><option>PEDIDO</option><option>GANHO</option><option>PERDIDO</option><option>CANCELADO</option></select></label>
      <Campo name="valor_estimado" label="Valor estimado" type="number" valor={String(dados.valor_estimado || dados.valor || 0)}/><Campo name="probabilidade" label="Probabilidade (%)" type="number" valor={String(dados.probabilidade || 0)}/><Campo name="equipamento" label="Equipamento" valor={equipamentoExibido}/><Campo name="data_fechamento_prevista" label="Fechamento previsto" type="date" valor={texto(dados.data_fechamento_prevista).slice(0,10)}/><Campo name="municipio" label="Município" valor={municipioExibido}/><Campo name="estado" label="UF" valor={estadoExibido}/>
      <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição comercial</span><textarea name="descricao" defaultValue={contexto.descricao} rows={6} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label><button disabled={salvando} className="flex min-h-14 items-center justify-center gap-2 rounded-2xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-60 sm:col-span-2">{salvando ? <Loader2 className="animate-spin"/> : <Save size={20}/>}Salvar alterações</button>
    </form>}
  </div></main>
}

function Campo({ name, label, valor, type = "text", required = false }: { name: string; label: string; valor: string; type?: string; required?: boolean }) { return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} defaultValue={valor} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label> }
