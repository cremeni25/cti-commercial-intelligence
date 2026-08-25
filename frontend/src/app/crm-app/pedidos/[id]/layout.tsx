"use client"

import type { ReactNode } from "react"
import { useParams } from "next/navigation"
import PrimeiraPaginaPedido from "@/components/propostas/PrimeiraPaginaPedido"

export default function PedidoCrmLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  return <>{children}{id && <div className="bg-[#020817] px-4 pb-28 text-white sm:px-6"><div className="mx-auto max-w-4xl"><PrimeiraPaginaPedido pedidoId={id} /></div></div>}</>
}
