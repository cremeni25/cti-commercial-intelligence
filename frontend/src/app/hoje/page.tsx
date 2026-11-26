"use client"

import { Sun } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import CartoesHoje from "@/components/hoje/CartoesHoje"
import { useAuth } from "@/core/auth"

export default function HojePage() {
  const { usuario } = useAuth()
  const nome = String(usuario?.nome || "").trim().split(/\s+/)[0]
  const data = new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })
  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar/>
      <section className="min-w-0 flex-1">
        <Topbar/>
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">{data}</p>
            <h1 className="mt-2 flex items-center gap-2 text-3xl font-bold sm:text-4xl"><Sun className="text-amber-300"/> {nome ? `Bom trabalho, ${nome}` : "Hoje"}</h1>
            <p className="mt-2 max-w-3xl text-gray-400">O que fazer agora, em ordem. Cada cartão leva direto à tela certa. Para qualquer outra coisa, use o botão “Pergunte ao CTI”.</p>
          </header>
          <CartoesHoje/>
        </div>
      </section>
    </main>
  )
}
