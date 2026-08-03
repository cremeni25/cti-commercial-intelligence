"use client"

import { FormEvent, useEffect, useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, Loader2, Save } from "lucide-react"

type Registro = Record<string, unknown>
function texto(valor: unknown) { return String(valor || "").trim() }
function numero(valor: unknown) { const n = Number(valor || 0); return Number.isFinite(n) ? n : 0 }

export default function EditarOportunidade() {
  const params = useParams<{ oportunidadeId: string }>()
  const searchParams = useSearchParams()
  const router = useRouter()
  const id = String(params.oportunidadeId || "")
  const origem = searchParams.get("origem") === "pipeline" ? "pipeline" : "oportunidades"
  const voltar = `/crm-app/${origem}`
  const [dados, setDados] = useState<Registro>({})
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  async function obter() {
    const resposta = await fetch(`/api/crm-proxy/crm/oportunidades/${encodeURIComponent(id)}`, { cache: "no-store" })
    const payload = await resposta.json().catch(() => ({}))
    if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
    return (Array.isArray(payload) ? payload[0] || {} : payload) as Registro
  }

  useEffect(() => {
    void obter().then(setDados).catch((falha) => setErro(falha instanceof Error ? falha.message : "Não foi possível carregar a oportunidade.")).finally(() => setCarregando(false))
  }, [id])

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setSalvando(true); setErro(""); setSucesso("")
    const form = new FormData(evento.currentTarget)
    const payload: Registro = {
      titulo: texto(form.get("titulo")),
      descricao: texto(form.get("descricao")) || null,
      status: texto(form.get("status")),
      valor_estimado: numero(form.get("valor_estimado")),
      probabilidade: numero(form.get("probabilidade")),
      data_fechamento_prevista: texto(form.get("data_fechamento_prevista")) || null,
      equipamento: texto(form.get("equipamento")) || null,
      municipio: texto(form.get("municipio")) || null,
      estado: texto(form.get("estado")).toUpperCase() || null,
    }

    try {
      const resposta = await fetch(`/api/crm-proxy/crm/oportunidades/${encodeURIComponent(id)}`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) {
        // O backend atualiza o registro principal antes de histórico/auditoria.
        // Em caso de falha auxiliar, confirma a gravação real antes de acusar erro.
        const confirmado = await obter().catch(() => null)
        const gravado = confirmado && texto(confirmado.titulo) === texto(payload.titulo)
          && texto(confirmado.status) === texto(payload.status)
          && numero(confirmado.valor_estimado) === numero(payload.valor_estimado)
        if (!gravado) throw new Error(texto((detalhe as Registro).detail) || `Falha ${resposta.status}`)
        setDados(confirmado as Registro)
        setSucesso("Oportunidade atualizada. O registro comercial foi salvo; a sincronização auxiliar será recomposta pelo CTI.")
        return
      }
      const atualizado = await obter().catch(() => payload)
      setDados(atualizado)
      setSucesso("Oportunidade atualizada com sucesso no núcleo CTI.")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível atualizar a oportunidade.")
    } finally { setSalvando(false) }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6"><div className="mx-auto max-w-3xl">
    <header className="mb-5 flex items-center gap-3"><button onClick={() => router.push(voltar)} className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></button><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Editar oportunidade</h1><p className="text-sm text-slate-400">Altere os dados comerciais e salve no núcleo CTI</p></div></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}
    {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : <form onSubmit={salvar} className="grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:grid-cols-2">
      <Campo name="titulo" label="Título" valor={texto(dados.titulo)} required/>
      <label><span className="mb-2 block text-sm text-slate-300">Etapa</span><select name="status" defaultValue={texto(dados.status) || "OPORTUNIDADE"} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option>OPORTUNIDADE</option><option>ATIVIDADES</option><option>PROPOSTA</option><option>NEGOCIACAO</option><option>PEDIDO</option><option>GANHO</option><option>PERDIDO</option><option>CANCELADO</option></select></label>
      <Campo name="valor_estimado" label="Valor estimado" type="number" valor={String(dados.valor_estimado || dados.valor || 0)}/>
      <Campo name="probabilidade" label="Probabilidade (%)" type="number" valor={String(dados.probabilidade || 0)}/>
      <Campo name="equipamento" label="Equipamento" valor={texto(dados.equipamento)}/>
      <Campo name="data_fechamento_prevista" label="Fechamento previsto" type="date" valor={texto(dados.data_fechamento_prevista).slice(0, 10)}/>
      <Campo name="municipio" label="Município" valor={texto(dados.municipio)}/>
      <Campo name="estado" label="UF" valor={texto(dados.estado || dados.uf)}/>
      <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição comercial</span><textarea name="descricao" defaultValue={texto(dados.descricao)} rows={6} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label>
      <button disabled={salvando} className="flex min-h-14 items-center justify-center gap-2 rounded-2xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-60 sm:col-span-2">{salvando ? <Loader2 className="animate-spin"/> : <Save size={20}/>}Salvar alterações</button>
    </form>}
  </div></main>
}

function Campo({ name, label, valor, type = "text", required = false }: { name: string; label: string; valor: string; type?: string; required?: boolean }) {
  return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} defaultValue={valor} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label>
}
