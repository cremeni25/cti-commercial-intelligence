"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import CatalogoVitrineView from "@/components/catalogo/CatalogoVitrineView"

export default function CrmAppCatalogoPage() {
  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-5 flex items-center gap-3">
          <Link href="/crm-app" aria-label="Voltar ao início" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p>
            <h1 className="text-2xl font-bold">Catálogo de produtos</h1>
            <p className="text-sm text-slate-400">Consulte modelos e envie materiais ao cliente.</p>
          </div>
        </header>
        <CatalogoVitrineView compacto/>
      </div>
    </main>
  )
}
