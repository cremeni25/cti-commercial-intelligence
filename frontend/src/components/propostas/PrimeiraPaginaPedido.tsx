/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useState } from "react"
import PrimeiraPaginaProposta from "@/components/propostas/PrimeiraPaginaProposta"

export default function PrimeiraPaginaPedido({ pedidoId }: { pedidoId: string }) {
  const [propostaId, setPropostaId] = useState("")
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    async function carregar() {
      setErro("")
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/pedidos/${encodeURIComponent(pedidoId)}`, { cache: "no-store" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || "Não foi possível localizar a proposta de origem do pedido."))
      const id = String(payload?.proposta?.id || "").trim()
      if (!id) throw new Error("O pedido não possui proposta de origem disponível para edição documental.")
      if (ativo) setPropostaId(id)
    }
    void carregar().catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar o documento do pedido.") })
    return () => { ativo = false }
  }, [pedidoId])

  if (erro) return <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>
  if (!propostaId) return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4 text-sm text-slate-400">Carregando dados finais do documento do pedido...</div>
  return <PrimeiraPaginaProposta propostaId={propostaId} compacto />
}
