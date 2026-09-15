"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import CicloComercial from "@/components/crm/CicloComercial"
import OportunidadeItensComerciais from "@/components/crm/OportunidadeItensComerciais"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>

function texto(valor: unknown) { return String(valor ?? "").trim() }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const item = payload as Registro
    for (const chave of ["dados", "itens", "oportunidades", "resultado"]) {
      if (Array.isArray(item[chave])) return item[chave] as Registro[]
    }
  }
  return []
}
function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function data(valor: unknown) { const v = texto(valor); if (!v) return "Não informado"; const d = new Date(v); return Number.isNaN(d.getTime()) ? v : d.toLocaleDateString("pt-BR") }
function diasDesde(valor: unknown) { const v = texto(valor); if (!v) return null; const d = new Date(v); if (Number.isNaN(d.getTime())) return null; return Math.max(0, Math.floor((Date.now() - d.getTime()) / 86400000)) }

export default function OportunidadeCrmAppPage() {
  const params = useParams<{ oportunidadeId: string }>()
  const id = String(params?.oportunidadeId || "")
  const [registro, setRegistro] = useState<Registro | null>(null)
  const [propostas, setPropostas] = useState<Registro[]>([])
  const [pedidos, setPedidos] = useState<Registro[]>([])
  const [vendas, setVendas] = useState<Registro[]>([])
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    if (!id) return
    let ativo = true
    Promise.all([
      fetchCrmSeguroProxy("crm-seguro/nucleo-comercial", { cache: "no-store" }).then((r) => r.json().then((p) => ({ r, p }))),
      fetch("/api/crm-proxy/crm-documentos/propostas", { cache: "no-store" }).then((r) => r.json().catch(() => [])),
      fetch("/api/crm-proxy/crm-documentos/pedidos", { cache: "no-store" }).then((r) => r.json().catch(() => [])),
      fetch("/api/crm-proxy/vendas", { cache: "no-store" }).then((r) => r.json().catch(() => [])),
    ]).then(([nucleo, prop, ped, vend]) => {
      if (!nucleo.r.ok) throw new Error(texto((nucleo.p as Registro)?.detail) || "Não foi possível carregar o negócio.")
      const oportunidade = lista(nucleo.p).find((item) => texto(item.oportunidade_id || item.id) === id)
      if (!oportunidade) throw new Error("Negócio não encontrado no seu escopo comercial.")
      if (!ativo) return
      setRegistro(oportunidade)
      setPropostas(lista(prop).filter((item) => texto(item.oportunidade_id) === id))
      setPedidos(lista(ped).filter((item) => texto(item.oportunidade_id) === id))
      setVendas(lista(vend).filter((item) => texto(item.oportunidade_id) === id))
    }).catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar o negócio.") })
      .finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [id])

  const clienteId = texto(registro?.cliente_id)
  const clienteNome = texto(registro?.cliente_nome) || "Cliente"
  const abertura = registro?.created_at || registro?.data_abertura || registro?.criado_em
  const dias = useMemo(() => diasDesde(abertura), [abertura])

  return <main className="min-h-screen bg-[#020817] px-4 pb-28 pt-5 text-white sm:px-6">
    <div className="mx-auto w-full max-w-4xl space-y-4">
      <header className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
        <Link href="/crm-app/oportunidades" className="text-sm font-semibold text-cyan-300">← Voltar aos negócios</Link>
        <p className="mt-4 text-xs font-bold uppercase tracking-[.18em] text-cyan-400">CTI CRM · negócio</p>
        <h1 className="mt-2 text-2xl font-bold">{texto(registro?.titulo) || "Oportunidade comercial"}</h1>
        <p className="mt-1 text-slate-400">{clienteNome}</p>
      </header>

      {carregando && <div className="rounded-3xl border border-[#16325c] bg-[#07162b] p-6 text-slate-300">Carregando ciclo comercial...</div>}
      {erro && <div className="rounded-3xl border border-red-900 bg-red-950/30 p-5 text-red-200">{erro}</div>}

      {registro && <>
        <CicloComercial registro={registro} propostas={propostas.length} pedidos={pedidos.length} vendas={vendas.length} />

        <section className="grid grid-cols-2 gap-3">
          <Kpi titulo="Valor" valor={moeda(registro.valor || registro.valor_estimado)} />
          <Kpi titulo="Ciclo aberto" valor={dias === null ? "—" : `${dias} dia${dias === 1 ? "" : "s"}`} />
          <Kpi titulo="Fechamento previsto" valor={data(registro.data_fechamento_prevista)} />
          <Kpi titulo="Responsável" valor={texto(registro.responsavel_nome || registro.responsavel) || "Você"} />
        </section>

        <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
          <p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">Próximo passo</p>
          <h2 className="mt-2 text-xl font-bold">Evoluir o negócio</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Se houve avanço comercial, gere a proposta a partir dos itens da oportunidade. Se ainda estiver em acompanhamento, registre apenas a próxima interação.</p>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            <a href="#proposta" className="flex min-h-14 items-center justify-center rounded-2xl bg-cyan-400 px-4 font-bold text-slate-950">Elaborar proposta</a>
            <Link href={`/crm-app/acao/registrar?cliente=${encodeURIComponent(clienteId || clienteNome)}&tipo=FOLLOW_UP`} className="flex min-h-14 items-center justify-center rounded-2xl border border-[#24466f] px-4 font-semibold text-cyan-200">Registrar continuidade</Link>
          </div>
        </section>

        <section id="proposta" className="scroll-mt-24 rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:p-5">
          <div className="mb-4">
            <p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">Proposta comercial</p>
            <h2 className="mt-2 text-xl font-bold">Itens, condições e proposta</h2>
            <p className="mt-1 text-sm text-slate-400">A mesma negociação é usada no CTI Web e no CRM App.</p>
          </div>
          <OportunidadeItensComerciais oportunidadeId={id} />
        </section>
      </>}
    </div>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><p className="text-xs text-slate-500">{titulo}</p><p className="mt-2 break-words text-sm font-bold text-cyan-200">{valor}</p></div>
}
