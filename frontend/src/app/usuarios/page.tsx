/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useMemo, useState } from "react"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { listarUsuarios } from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI } from "@/modules/usuarios/types/usuario.types"

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [usuarios, setUsuarios] = useState<UsuarioCTI[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const perfil = String(usuario?.tipo_usuario || "").toUpperCase()
  const autorizado = perfil === "ADMIN_MASTER"

  useEffect(() => {
    if (authLoading) return
    if (!autorizado) {
      setLoading(false)
      return
    }

    let ativo = true
    setLoading(true)
    setError("")

    void listarUsuarios()
      .then((dados) => {
        if (ativo) setUsuarios(dados)
      })
      .catch((erro) => {
        if (ativo) setError(erro instanceof Error ? erro.message : "Não foi possível carregar os usuários.")
      })
      .finally(() => {
        if (ativo) setLoading(false)
      })

    return () => {
      ativo = false
    }
  }, [authLoading, autorizado])

  const totais = useMemo(() => {
    const ativos = usuarios.filter((item) => item.ativo).length
    const perfis = new Set(usuarios.map((item) => item.tipo_usuario).filter(Boolean)).size
    return { total: usuarios.length, ativos, perfis }
  }, [usuarios])

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-6 lg:p-8">
          <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">CTI Administração</p>
            <h1 className="mt-3 text-3xl font-bold lg:text-4xl">Usuários e permissões</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
              Gestão central de contas, perfis, empresas, cargos e situação de acesso ao CTI.
            </p>
          </header>

          {authLoading || loading ? (
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">Carregando usuários e permissões...</div>
          ) : !autorizado ? (
            <div className="rounded-3xl border border-red-900/60 bg-red-950/20 p-8">
              <h2 className="text-xl font-bold text-red-300">Acesso não autorizado</h2>
              <p className="mt-2 text-sm text-red-100/70">Este módulo é exclusivo do perfil ADMIN_MASTER.</p>
            </div>
          ) : (
            <>
              {error && <div className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{error}</div>}

              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="Usuários cadastrados" value={String(totais.total)} />
                <Metric label="Usuários ativos" value={String(totais.ativos)} />
                <Metric label="Perfis em uso" value={String(totais.perfis)} />
              </div>

              <section className="overflow-hidden rounded-3xl border border-[#13203f] bg-[#071427]">
                <div className="border-b border-[#13203f] px-6 py-5">
                  <h2 className="text-lg font-bold">Contas cadastradas</h2>
                  <p className="mt-1 text-sm text-slate-400">Consulta operacional das contas existentes em cti_users.</p>
                </div>

                {usuarios.length === 0 ? (
                  <div className="p-8 text-sm text-slate-400">Nenhum usuário foi localizado para o perfil autenticado.</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-left text-sm">
                      <thead className="bg-[#061326] text-xs uppercase tracking-wider text-slate-500">
                        <tr>
                          <th className="px-6 py-4">Usuário</th>
                          <th className="px-6 py-4">Empresa</th>
                          <th className="px-6 py-4">Cargo</th>
                          <th className="px-6 py-4">Perfil</th>
                          <th className="px-6 py-4">Situação</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#13203f]">
                        {usuarios.map((item) => (
                          <tr key={item.id} className="hover:bg-white/[0.02]">
                            <td className="px-6 py-4">
                              <div className="font-semibold text-white">{item.nome || "Sem nome"}</div>
                              <div className="mt-1 text-xs text-slate-500">{item.email}</div>
                            </td>
                            <td className="px-6 py-4 text-slate-300">{item.empresa || "—"}</td>
                            <td className="px-6 py-4 text-slate-300">{item.cargo || "—"}</td>
                            <td className="px-6 py-4"><span className="rounded-full border border-cyan-900 bg-cyan-950/40 px-3 py-1 text-xs font-semibold text-cyan-300">{item.tipo_usuario || "NÃO DEFINIDO"}</span></td>
                            <td className="px-6 py-4"><span className={`rounded-full border px-3 py-1 text-xs font-semibold ${item.ativo ? "border-emerald-900 bg-emerald-950/40 text-emerald-300" : "border-red-900 bg-red-950/30 text-red-300"}`}>{item.ativo ? "ATIVO" : "INATIVO"}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#13203f] bg-[#071427] p-5">
      <div className="text-xs uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mt-2 text-xl font-bold text-cyan-300">{value}</div>
    </div>
  )
}
