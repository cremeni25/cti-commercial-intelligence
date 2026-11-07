"use client"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import CatalogoVitrineView from "@/components/catalogo/CatalogoVitrineView"

export default function CatalogoPage() {
  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar/>
      <section className="min-w-0 flex-1">
        <Topbar/>
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">Conhecimento comercial</p>
            <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Catálogo de produtos</h1>
            <p className="mt-2 max-w-2xl text-gray-400">Modelos Carrier Transicold por linha, com materiais de divulgação prontos para enviar ao cliente.</p>
          </header>
          <CatalogoVitrineView/>
        </div>
      </section>
    </main>
  )
}
