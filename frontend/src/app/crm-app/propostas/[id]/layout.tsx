"use client"

import type { ReactNode } from "react"
import { useParams } from "next/navigation"
import PrimeiraPaginaProposta from "@/components/propostas/PrimeiraPaginaProposta"

export default function PropostaCrmLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")

  return <>
    {id && <div className="bg-[#020817] px-4 pt-5 text-white sm:px-6"><div className="mx-auto max-w-4xl"><PrimeiraPaginaProposta propostaId={id} compacto /></div></div>}
    {children}
  </>
}
