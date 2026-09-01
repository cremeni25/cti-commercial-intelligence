"use client"

import type { ReactNode } from "react"
import { useParams } from "next/navigation"
import PrimeiraPaginaProposta from "@/components/propostas/PrimeiraPaginaProposta"

export default function PropostaLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  return <>
    <div className="[&>main]:!min-h-0">{children}</div>
    {id && <div className="bg-[#020817] px-4 pb-8 text-white sm:px-6 lg:pl-[calc(16rem+2rem)] lg:pr-8"><PrimeiraPaginaProposta propostaId={id} /></div>}
  </>
}
