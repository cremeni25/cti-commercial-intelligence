/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { criarUsuario, listarUsuarios, type NovoUsuarioCTI } from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI } from "@/modules/usuarios/types/usuario.types"

const formularioInicial: NovoUsuarioCTI = {
  nome: "",
  email: "",
  senha: "",
  empresa: "Viena SP",
  cargo: "",
  tipo_usuario: "DIRETOR",
  territorio: "Brasil",
  ddds: [],
  superior_id: undefined,
}

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [usuarios, setUsuarios] = useState<UsuarioCTI[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [salvando, setSalvando] = useState(false)
  const [novo, setNovo] = useState<NovoUsuarioCTI>(formularioInicial)
  const [dddsTexto, setDddsTexto] = useState("")

  const perfil = String(usuario?.tipo_usuario || "").toUpperCase()
  const autorizado = perfil === "ADMIN_MASTER"

  async function carregar() {
    setLoading(true)
    setError("")
    try {
      setUsuarios(await listarUsuarios())
    } catch (erro) {
      setError(erro instanceof Error ? erro.message : "Não foi possível carregar os usuários.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (authLoading) return
    if (!autorizado) {
      setLoading(false)
      return
    }
    void carregar()
  }, [authLoading, autorizado])

  async function cadastrar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setMensagem("")
    setSalvando(true)
    try {
      await criarUsuario({
        ...novo,
        ddds: dddsTexto.split(",").map((item) => item.trim()).filter(Boolean),
        superior_id: novo.superior_id || undefined,
      })
      setMensagem("Usuário criado no Supabase Auth e vinculado ao organograma do CTI.")
      setNovo(formularioInicial)
      setDddsTexto("")
      await carregar()
    } catch (erro) {
      setError(erro instanceof Error ? erro.message : "Não foi possível criar o usuário.")
    } finally {
      setSalvando(false)
    }
  }

  const totais = useMemo(() => {
    const ativos = usuarios.filter((item) => item.ativo).length
    const perfis = new Set(usuarios.map((item) => item.tipo_usuario).filter(Boolean)).size
    return { total: usuarios.length, ativos, perfis }
  }, [usuarios])

  const superiores = usuarios.filter((item) => item.ativo && ["ADMIN_MASTER", "DIRETOR", "GESTOR_REGIONAL", "GERENTE"].includes(String(item.tipo_usuario)))

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-6 lg:p-8">
          <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">CTI Administração</p>
            <h1 className="mt-3 text-3xl font-bold lg:text-4xl">Usuários, funções e permissões</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">Gestão central de contas, organograma, empresas, cargos, territórios e situação de acesso.</p>
          </header>

          {authLoading || loading ? (
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">Carregando usuários e permissões...</div>
          ) : !autorizado ? (
            <div className="rounded-3xl border border-red-900/60 bg-red-950/20 p-8"><h2 className="text-xl font-bold text-red-300">Acesso não autorizado</h2><p className="mt-2 text-sm text-red-100/70">Este módulo é exclusivo do perfil ADMIN_MASTER.</p></div>
          ) : (
            <>
              {mensagem && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/30 px-5 py-4 text-sm text-emerald-200">{mensagem}</div>}
              {error && <div className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{error}</div>}

              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="Usuários cadastrados" value={String(totais.total)} />
                <Metric label="Usuários ativos" value={String(totais.ativos)} />
                <Metric label="Perfis em uso" value={String(totais.perfis)} />
              </div>

              <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
                <div className="mb-5"><h2 className="text-xl font-bold">Cadastrar usuário</h2><p className="mt-1 text-sm text-slate-400">A conta será criada no Supabase Auth e vinculada ao organograma do CTI.</p></div>
                <form onSubmit={cadastrar} className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <Campo label="Nome completo" value={novo.nome} onChange={(v) => setNovo({ ...novo, nome: v })} />
                  <Campo label="E-mail" type="email" value={novo.email} onChange={(v) => setNovo({ ...novo, email: v })} />
                  <Campo label="Senha inicial" type="password" value={novo.senha} onChange={(v) => setNovo({ ...novo, senha: v })} />
                  <Campo label="Empresa" value={novo.empresa} onChange={(v) => setNovo({ ...novo, empresa: v })} />
                  <Campo label="Cargo institucional" value={novo.cargo} onChange={(v) => setNovo({ ...novo, cargo: v })} />
                  <label className="text-sm text-slate-300">Perfil
                    <select value={novo.tipo_usuario} onChange={(e) => setNovo({ ...novo, tipo_usuario: e.target.value as NovoUsuarioCTI["tipo_usuario"] })} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white">
                      <option value="DIRETOR">DIRETOR</option><option value="GESTOR_REGIONAL">GESTOR_REGIONAL</option><option value="VENDEDOR_REGIONAL">VENDEDOR_REGIONAL</option><option value="GERENTE">GERENTE</option><option value="VENDEDOR">VENDEDOR</option>
                    </select>
                  </label>
                  <Campo label="Território" value={novo.territorio || ""} onChange={(v) => setNovo({ ...novo, territorio: v })} />
                  <Campo label="DDDs autorizados" value={dddsTexto} onChange={setDddsTexto} placeholder="011, 012, 013" />
                  <label className="text-sm text-slate-300">Superior no organograma
                    <select value={novo.superior_id || ""} onChange={(e) => setNovo({ ...novo, superior_id: e.target.value || undefined })} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white">
                      <option value="">Sem superior definido</option>
                      {superiores.map((item) => <option key={item.id} value={item.id}>{item.nome} — {item.tipo_usuario}</option>)}
                    </select>
                  </label>
                  <button disabled={salvando} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60 md:col-span-2 xl:col-span-3">{salvando ? "Criando usuário..." : "Criar usuário e credenciais"}</button>
                </form>
              </section>

              <section className="overflow-hidden rounded-3xl border border-[#13203f] bg-[#071427]">
                <div className="border-b border-[#13203f] px-6 py-5"><h2 className="text-lg font-bold">Contas cadastradas</h2><p className="mt-1 text-sm text-slate-400">Hierarquia: ADMIN_MASTER → DIRETOR → GESTOR_REGIONAL → VENDEDOR_REGIONAL.</p></div>
                {usuarios.length === 0 ? <div className="p-8 text-sm text-slate-400">Nenhum usuário cadastrado.</div> : (
                  <div className="overflow-x-auto"><table className="min-w-full text-left text-sm"><thead className="bg-[#061326] text-xs uppercase tracking-wider text-slate-500"><tr><th className="px-6 py-4">Usuário</th><th className="px-6 py-4">Empresa</th><th className="px-6 py-4">Cargo</th><th className="px-6 py-4">Perfil</th><th className="px-6 py-4">Situação</th></tr></thead><tbody className="divide-y divide-[#13203f]">{usuarios.map((item) => <tr key={item.id} className="hover:bg-white/[0.02]"><td className="px-6 py-4"><div className="font-semibold text-white">{item.nome || "Sem nome"}</div><div className="mt-1 text-xs text-slate-500">{item.email}</div></td><td className="px-6 py-4 text-slate-300">{item.empresa || "—"}</td><td className="px-6 py-4 text-slate-300">{item.cargo || "—"}</td><td className="px-6 py-4"><span className="rounded-full border border-cyan-900 bg-cyan-950/40 px-3 py-1 text-xs font-semibold text-cyan-300">{item.tipo_usuario || "NÃO DEFINIDO"}</span></td><td className="px-6 py-4"><span className={`rounded-full border px-3 py-1 text-xs font-semibold ${item.ativo ? "border-emerald-900 bg-emerald-950/40 text-emerald-300" : "border-red-900 bg-red-950/30 text-red-300"}`}>{item.ativo ? "ATIVO" : "INATIVO"}</span></td></tr>)}</tbody></table></div>
                )}
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#071427] p-5"><div className="text-xs uppercase tracking-wider text-slate-500">{label}</div><div className="mt-2 text-xl font-bold text-cyan-300">{value}</div></div> }
function Campo({ label, value, onChange, type = "text", placeholder }: { label: string; value: string; onChange: (value: string) => void; type?: string; placeholder?: string }) { return <label className="text-sm text-slate-300">{label}<input type={type} required value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-white outline-none focus:border-cyan-400" /></label> }
