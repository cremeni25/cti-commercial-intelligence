"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, Loader2, Save } from "lucide-react"
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
  const searchParams = useSearchParams()
  const router = useRouter()
  const id = String(params.oportunidadeId || "")
  const origemParam = searchParams.get("origem") || "oportunidades"
  const origem = origemParam === "pipeline" ? "pipeline" : origemParam === "clientes" ? "clientes" : "oportunidades"
  const voltar = origem === "clientes" ? `/crm-app/historico/${id}?origem=clientes` : `/crm-app/${origem}`
  const [dados, setDados] = useState<Registro>({})
  const [clientes, setClientes] = useState<Registro[]>([])
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const contexto = useMemo(() => lerContextoOportunidade(dados), [dados])

  async function obter() {
    const resposta = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}`, { cache: "no-store" })
    const payload = await resposta.json().catch(() => ({}))
    if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
    return (Array.isArray(payload) ? payload[0] || {} : payload) as Registro
  }

  useEffect(() => {
    void Promise.all([
      obter(),
      fetch("/api/crm-proxy/crm-app/clientes", { cache: "no-store" }).then(async r => r.ok ? await r.json() : []),
    ]).then(([oportunidade, lista]) => { setDados(oportunidade); setClientes(Array.isArray(lista) ? lista : []) })
      .catch((falha) => setErro(falha instanceof Error ? falha.message : "Não foi possível carregar a oportunidade."))
      .finally(() => setCarregando(false))
  }, [id])

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setSalvando(true); setErro(""); setSucesso("")
    const form = new FormData(evento.currentTarget)
    const equipamento = texto(form.get("equipamento"))
    const municipio = texto(form.get("municipio"))
    const estado = texto(form.get("estado")).toUpperCase()
    const descricaoBase = texto(form.get("descricao"))
    const clienteId = texto(form.get("cliente_id"))
    const descricao = montarDescricaoComContexto(descricaoBase, { linhas: contexto.linhas, equipamentos: equipamento ? equipamento.split(",").map((item) => item.trim()).filter(Boolean) : contexto.equipamentos, quantidade: contexto.quantidade, municipio: municipio || contexto.municipio, uf: estado || contexto.uf, ddd: contexto.ddd, subRegiao: contexto.subRegiao })
    const payload: Registro = { titulo: texto(form.get("titulo")), descricao, status: texto(form.get("status")), valor_estimado: numero(form.get("valor_estimado")), probabilidade: numero(form.get("probabilidade")), data_fechamento_prevista: texto(form.get("data_fechamento_prevista")) || null, equipamento: equipamento || null, municipio: municipio || null, estado: estado || null }

    try {
      if (clienteId && clienteId !== texto(dados.cliente_id)) {
        const troca = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}/estabelecimento`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cliente_id: clienteId, motivo: "Estabelecimento/CNPJ selecionado para esta negociação." }) })
        const detalheTroca = await troca.json().catch(() => ({})) as Registro
        if (!troca.ok) throw new Error(texto(detalheTroca.detail) || `Falha ${troca.status}`)
      }
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/oportunidades/${encodeURIComponent(id)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto((detalhe as Registro).detail) || `Falha ${resposta.status}`)
      const atualizado = await obter().catch(() => ({ ...dados, ...payload, cliente_id: clienteId }))
      setDados(atualizado)
      setSucesso("Negociação atualizada. O CNPJ escolhido vale para esta negociação; cadastro mestre e documentos já emitidos permanecem preservados.")
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível atualizar a oportunidade.") }
    finally { setSalvando(false) }
  }

  const equipamentoExibido = texto(dados.equipamento) || contexto.equipamentos.join(", ")
  const municipioExibido = texto(dados.municipio) || contexto.municipio
  const estadoExibido = texto(dados.estado || dados.uf) || contexto.uf

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6"><div className="mx-auto max-w-3xl">
    <header className="mb-5 flex items-center gap-3"><button onClick={() => router.push(voltar)} className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></button><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Editar negociação</h1><p className="text-sm text-slate-400">Dados comerciais e estabelecimento desta negociação</p></div></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}
    {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : <form onSubmit={salvar} className="grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:grid-cols-2">
      <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Estabelecimento / CNPJ desta negociação</span><select name="cliente_id" defaultValue={texto(dados.cliente_id)} className="min-h-12 w-full rounded-2xl border border-cyan-800 bg-[#020817] px-4 py-3" required><option value="">Selecione o estabelecimento</option>{clientes.map((item) => { const cid=texto(item.id||item.cliente_id||item.uuid); return cid ? <option key={cid} value={cid}>{nomeCliente(item)}{cnpjCliente(item) ? ` — ${formatarCnpj(cnpjCliente(item))}` : ""}</option> : null })}</select><p className="mt-2 text-xs text-slate-500">A alteração vale somente para esta negociação. O histórico e documentos já emitidos não são reescritos.</p></label>
      <Campo name="titulo" label="Título" valor={texto(dados.titulo)} required/>
      <label><span className="mb-2 block text-sm text-slate-300">Etapa</span><select name="status" defaultValue={texto(dados.status) || "OPORTUNIDADE"} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option>OPORTUNIDADE</option><option>ATIVIDADES</option><option>PROPOSTA</option><option>NEGOCIACAO</option><option>PEDIDO</option><option>GANHO</option><option>PERDIDO</option><option>CANCELADO</option></select></label>
      <Campo name="valor_estimado" label="Valor estimado" type="number" valor={String(dados.valor_estimado || dados.valor || 0)}/><Campo name="probabilidade" label="Probabilidade (%)" type="number" valor={String(dados.probabilidade || 0)}/><Campo name="equipamento" label="Equipamento" valor={equipamentoExibido}/><Campo name="data_fechamento_prevista" label="Fechamento previsto" type="date" valor={texto(dados.data_fechamento_prevista).slice(0, 10)}/><Campo name="municipio" label="Município" valor={municipioExibido}/><Campo name="estado" label="UF" valor={estadoExibido}/>
      <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição comercial</span><textarea name="descricao" defaultValue={contexto.descricao} rows={6} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label>
      <button disabled={salvando} className="flex min-h-14 items-center justify-center gap-2 rounded-2xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-60 sm:col-span-2">{salvando ? <Loader2 className="animate-spin"/> : <Save size={20}/>}Salvar alterações</button>
    </form>}
  </div></main>
}

function Campo({ name, label, valor, type = "text", required = false }: { name: string; label: string; valor: string; type?: string; required?: boolean }) { return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} defaultValue={valor} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label> }
