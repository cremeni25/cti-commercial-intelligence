"use client"

import { useEffect, useMemo, useState } from "react"
import { ControlledSelect } from "@/components/crm-app/ControlledSelect"
import { dinheiro, texto } from "./financeiro"

type R = Record<string, unknown>
type E = { codigo: string; nome: string; preco: number }

export default function NovoItemFinanceiro({ oportunidadeId, ordem, onDone }: { oportunidadeId: string; ordem: number; onDone: () => void }) {
  const [lista, setLista] = useState<E[]>([])
  const [codigo, setCodigo] = useState("")
  const [qtd, setQtd] = useState(1)
  const [desc, setDesc] = useState(0)
  const [aberto, setAberto] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")

  useEffect(() => {
    fetch("/api/crm-proxy/catalogo-comercial/equipamentos", { cache: "no-store" })
      .then((r) => r.json())
      .then((p) => {
        const l = (Array.isArray(p) ? p : [])
          .map((x: R) => ({
            codigo: texto(x.codigo),
            nome: texto(x.nome_comercial || x.equipamento),
            preco: Number((x.preco_vigente as R)?.preco_cheio || 0),
          }))
          .filter((x) => x.codigo)
        setLista(l)
        if (l[0]) setCodigo(l[0].codigo)
      })
      .catch(() => setErro("Falha ao carregar catálogo."))
  }, [])

  const equipamento = useMemo(() => lista.find((x) => x.codigo === codigo), [lista, codigo])
  const unitario = (equipamento?.preco || 0) * (1 - desc / 100)
  const total = unitario * qtd
  const opcoes = useMemo(() => lista.map((x) => [x.codigo, x.nome] as const), [lista])

  async function salvar() {
    if (!equipamento || salvando) return
    setErro("")
    setSalvando(true)
    try {
      const r = await fetch(`/api/crm-proxy/catalogo-comercial/oportunidades/${encodeURIComponent(oportunidadeId)}/itens`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equipamento_codigo: equipamento.codigo,
          quantidade: qtd,
          desconto_percentual: desc,
          ordem,
        }),
      })
      const p = await r.json().catch(() => ({}))
      if (!r.ok) {
        setErro(texto((p as R).detail) || `Não foi possível salvar o item (${r.status}).`)
        return
      }
      setAberto(false)
      setQtd(1)
      setDesc(0)
      onDone()
    } finally {
      setSalvando(false)
    }
  }

  if (!aberto) {
    return (
      <button type="button" onClick={() => setAberto(true)} className="mt-4 w-full rounded-xl border border-cyan-700 px-4 py-3 font-semibold text-cyan-300">
        + Adicionar outro item
      </button>
    )
  }

  return (
    <div className="mt-4 rounded-2xl border border-[#24466f] bg-[#061326] p-4">
      <div>
        <h3 className="font-bold">Novo item da mesma intenção de compra</h3>
        <p className="mt-1 text-xs text-slate-400">Cada equipamento cadastrado aqui permanece na mesma oportunidade e poderá gerar sua própria proposta Carrier.</p>
      </div>

      {erro && <p className="mt-3 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{erro}</p>}

      <label className="mt-4 block text-xs text-slate-300">
        Equipamento
        <div className="mt-1">
          <ControlledSelect value={codigo} onChange={setCodigo} options={opcoes} buttonClassName="rounded-xl" />
        </div>
      </label>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="text-xs text-slate-300">
          Quantidade
          <input
            type="number"
            min={1}
            value={qtd}
            onChange={(x) => setQtd(Math.max(1, Number(x.target.value) || 1))}
            className="mt-1 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3"
          />
        </label>
        <label className="text-xs text-slate-300">
          Desconto (%)
          <input
            type="number"
            min={0}
            max={100}
            step="0.01"
            value={desc}
            onChange={(x) => setDesc(Math.max(0, Math.min(100, Number(x.target.value) || 0)))}
            className="mt-1 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3"
          />
        </label>
      </div>

      <div className="mt-3 rounded-xl border border-[#16325c] bg-[#020817] p-3 text-sm text-slate-300">
        <div>Tabela unitária: <strong className="text-white">{dinheiro(equipamento?.preco)}</strong></div>
        <div>Desconto por unidade: <strong className="text-white">{dinheiro((equipamento?.preco || 0) - unitario)}</strong></div>
        <div>Unitário negociado: <strong className="text-emerald-300">{dinheiro(unitario)}</strong></div>
        <div>Subtotal deste item: <strong className="text-emerald-300">{dinheiro(total)}</strong></div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <button type="button" disabled={salvando} onClick={() => setAberto(false)} className="rounded-xl border border-[#24466f] py-3 disabled:opacity-50">Cancelar</button>
        <button type="button" disabled={salvando || !equipamento} onClick={() => void salvar()} className="rounded-xl bg-cyan-500 py-3 font-bold text-slate-950 disabled:opacity-50">
          {salvando ? "Salvando..." : "Salvar item"}
        </button>
      </div>
    </div>
  )
}
