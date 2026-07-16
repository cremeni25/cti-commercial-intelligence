"use client"

import Link from "next/link"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

export default function DashboardHub() {
  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-white">
              HUB CTI
            </h1>
            <p className="text-gray-400 mt-2">
              Selecione uma visão operacional. O hub não soma bases de contextos diferentes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Link
              href="/brasil"
              className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-6 text-white hover:bg-cyan-500/20"
            >
              <h2 className="text-2xl font-bold">Brasil</h2>
              <p className="text-gray-300 mt-2">Visão nacional alimentada apenas pela aba Brasil.</p>
            </Link>

            <Link
              href="/autorizados/viena-sp"
              className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-6 text-white hover:bg-emerald-500/20"
            >
              <h2 className="text-2xl font-bold">Viena SP</h2>
              <p className="text-gray-300 mt-2">Visão regional do autorizado Viena, anos 2025 e 2026.</p>
            </Link>
          </div>

          <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-gray-300">
            Nenhum alerta operacional calculado.
          </div>
        </div>
      </section>
    </main>
  )
}
