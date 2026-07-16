"use client"

import Link from "next/link"

export default function ImplementadorasPage() {
  return (
    <main className="min-h-screen bg-[#020817] p-8 text-white">
      <h1 className="text-3xl font-bold">Implementadoras</h1>
      <p className="text-gray-400 mt-2">Escolha o contexto operacional. Brasil e Viena SP não são consolidados automaticamente.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <Link href="/brasil" className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-6 hover:bg-cyan-500/20">Implementadoras Brasil</Link>
        <Link href="/autorizados/viena-sp" className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-6 hover:bg-emerald-500/20">Implementadoras Viena SP</Link>
      </div>
    </main>
  )
}
