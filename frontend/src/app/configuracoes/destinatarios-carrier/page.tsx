/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useCallback, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Destinatario = {
  id: string
  nome: string
  email: string
  cargo?: string
  ativo: boolean
}

export default function DestinatariosAdministrativosPage() {
  const [dados, setDados] = useState<Destinatario[]>([])
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [loading, setLoading] = useState(true)
  const [salvando, setSalvando] = useState(false)

  const carregar = useCallback(async () => {
    setLoading(true)
    setErro("")
    try {
      const response = await fetch(`${API_URL}/carrier-operacional/destinatarios`, { cache: "no-store" })
      const payload = await response.json().catch(() => [])
      if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar os destinatários.")
      setDados(Array.isArray(payload) ? payload : [])
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao carregar os destinatários.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void carregar() }, [carregar])

  async function criar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true)
    setErro("")
    setMensagem("")
    const formulario = evento.currentTarget
    const dadosForm = new FormData(formulario)
    const payload = {
      nome: String(dadosForm.get("nome") || "").trim(),
      email: String(dadosForm.get("email") || "").trim(),
      cargo: String(dadosForm.get("cargo") || "").trim() || null,
      ativo: true,
    }
    try {
      const response = await fetch(`${API_URL}/carrier-operacional/destinatarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const retorno = await response.json().catch(() => null)
      if (!response.ok) throw new Error(retorno?.detail || "Não foi possível cadastrar o destinatário.")
      formulario.reset()
      setMensagem("Destinatário cadastrado.")
      await carregar()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao cadastrar destinatário.")
    } finally {
      setSalvando(false)
    }
  }

  async function alternar(destinatario: Destinatario) {
    setErro("")
    const response = await fetch(`${API_URL}/carrier-operacional/destinatarios/${destinatario.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ativo: !destinatario.ativo }),
    })
    const retorno = await response.json().catch(() => null)
    if (!response.ok) {
      setErro(retorno?.detail || "Não foi possível alterar o destinatário.")
      return
    }
    setMensagem(destinatario.ativo ? "Destinatário desativado." : "Destinatário reativado.")
    await carregar()
  }

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Comunicações comerciais</p>
          <h1 className="mt-2 text-3xl font-bold">Destinatários administrativos</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-400">Cadastre as pessoas que poderão ser selecionadas em cada envio. O remetente decide, no momento do envio, quem receberá a mensagem.</p>
        </header>

        {erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}
        {mensagem && <div className="rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}

        <form onSubmit={criar} className="grid gap-4 rounded-3xl border border-[#13203f] bg-[#071427] p-6 md:grid-cols-3">
          <Campo nome="nome" label="Nome" required />
          <Campo nome="email" label="E-mail" type="email" required />
          <Campo nome="cargo" label="Cargo" />
          <button disabled={salvando} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60 md:col-span-3">{salvando ? "Salvando..." : "Cadastrar destinatário"}</button>
        </form>

        <section className="overflow-hidden rounded-3xl border border-[#13203f] bg-[#071427]">
          <div className="border-b border-[#13203f] p-6"><h2 className="text-xl font-bold">Cadastro atual</h2></div>
          {loading ? <p className="p-6 text-slate-400">Carregando...</p> : dados.length === 0 ? <p className="p-6 text-slate-500">Nenhum destinatário cadastrado.</p> : <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-[#091a33] text-left text-slate-400"><tr><th className="p-4">Nome</th><th className="p-4">E-mail</th><th className="p-4">Cargo</th><th className="p-4">Status</th><th className="p-4">Ação</th></tr></thead><tbody>{dados.map((item) => <tr key={item.id} className="border-t border-[#13203f]"><td className="p-4 font-semibold">{item.nome}</td><td className="p-4 text-cyan-300">{item.email}</td><td className="p-4 text-slate-300">{item.cargo || "-"}</td><td className="p-4"><span className={`rounded-full border px-3 py-1 text-xs ${item.ativo ? "border-emerald-800 text-emerald-300" : "border-slate-700 text-slate-400"}`}>{item.ativo ? "ATIVO" : "INATIVO"}</span></td><td className="p-4"><button onClick={() => void alternar(item)} className="rounded-lg border border-cyan-800 px-3 py-2 text-xs text-cyan-300">{item.ativo ? "Desativar" : "Reativar"}</button></td></tr>)}</tbody></table></div>}
        </section>
      </div>
    </section>
  </main>
}

function Campo({ nome, label, type = "text", required = false }: { nome: string; label: string; type?: string; required?: boolean }) {
  return <label className="text-sm text-slate-300">{label}<input name={nome} type={type} required={required} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label>
}
