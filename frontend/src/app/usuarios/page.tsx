/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import {
  criarUsuario,
  listarUsuarios,
  type PerfilCTI,
  type UsuarioNovo,
} from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI } from "@/modules/usuarios/types/usuario.types"

const perfis: { valor: PerfilCTI; rotulo: string }[] = [
  { valor: "DIRETOR_VIENA_SP", rotulo: "Diretor VIENA SP" },
  { valor: "ADMIN_COMERCIAL_VIENA_SP", rotulo: "Admin Comercial VIENA SP" },
  { valor: "ADMIN_FINANCEIRO_VIENA_SP", rotulo: "Admin Financeiro VIENA SP" },
  { valor: "INDICADOR_VIENA_SP", rotulo: "Indicador VIENA SP" },
  { valor: "REPRES_REGIAO_01", rotulo: "Representante Região 01" },
  { valor: "REPRES_REGIAO_02", rotulo: "Representante Região 02" },
]

const usuarioInicial: UsuarioNovo = {
  nome: "",
  email: "",
  senha_temporaria: "",
  empresa: "VIENA SP",
  tipo_usuario: "DIRETOR_VIENA_SP",
  territorio: "Viena SP",
  ddds: [],
}

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [usuarios, setUsuarios] = useState<UsuarioCTI[]>([])
  const [novo, setNovo] = useState<UsuarioNovo>(usuarioInicial)
  const [dddsTexto, setDddsTexto] = useState("")
  const [mostrarNovo, setMostrarNovo] = useState(false)
  const [loading, setLoading] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")

  const autorizado = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"

  async function carregar() {
    setLoading(true)
    setErro("")
    try {
      setUsuarios(await listarUsuarios())
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível carregar os usuários.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (authLoading) return
    if (!autorizado) return setLoading(false)
    void carregar()
  }, [authLoading, autorizado])

  async function cadastrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setProcessando(true)
    setErro("")
    setMensagem("")
    try {
      await criarUsuario({
        ...novo,
        email: novo.email.trim().toLowerCase(),
        ddds: dddsTexto.split(",").map((item) => item.trim()).filter(Boolean),
      })
      setMensagem("Usuário criado com senha temporária. No primeiro acesso, a troca de senha e a conclusão do cadastro serão obrigatórias.")
      setNovo(usuarioInicial)
      setDddsTexto("")
      setMostrarNovo(false)
      await carregar()
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Não foi possível criar o usuário.")
    } finally {
      setProcessando(false)
    }
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6 lg:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">CTI Administração</p>
            <div className="mt-3 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <h1 className="text-3xl font-bold">Governança de usuários e acessos</h1>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">Somente pessoas reais com e-mail e conta de autenticação são contabilizadas como usuários do CTI.</p>
              </div>
              {autorizado && (
                <button type="button" onClick={() => setMostrarNovo(!mostrarNovo)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">
                  {mostrarNovo ? "Fechar cadastro" : "Criar usuário"}
                </button>
              )}
            </div>
          </header>

          {authLoading || loading ? <Aviso>Carregando usuários reais...</Aviso> : !autorizado ? <Aviso>Este módulo é exclusivo do ADMIN_MASTER.</Aviso> : (
            <>
              {mensagem && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/30 px-5 py-4 text-sm text-emerald-200">{mensagem}</div>}
              {erro && <div className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</div>}

              {mostrarNovo && (
                <form onSubmit={cadastrar} className="rounded-3xl border border-cyan-900 bg-[#071427] p-5 sm:p-6">
                  <h2 className="text-xl font-bold">Novo usuário CTI</h2>
                  <p className="mt-1 text-sm text-slate-400">O ADMIN_MASTER define a função. O usuário entra com senha temporária, troca a senha e completa o cadastro.</p>
                  <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    <Campo label="Nome completo" value={novo.nome} onChange={(value) => setNovo({ ...novo, nome: value })} required />
                    <Campo label="E-mail" type="email" value={novo.email} onChange={(value) => setNovo({ ...novo, email: value })} required />
                    <Campo label="Senha temporária" type="password" value={novo.senha_temporaria} onChange={(value) => setNovo({ ...novo, senha_temporaria: value })} placeholder="Mínimo 8 caracteres" required />
                    <Select label="Função oficial" value={novo.tipo_usuario} onChange={(value) => setNovo({ ...novo, tipo_usuario: value as PerfilCTI })} options={perfis} />
                    <Campo label="Território" value={novo.territorio || ""} onChange={(value) => setNovo({ ...novo, territorio: value })} />
                    <Campo label="DDDs autorizados" value={dddsTexto} onChange={setDddsTexto} placeholder="011, 012, 013" />
                  </div>
                  <button disabled={processando} className="mt-5 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60">
                    {processando ? "Criando..." : "Criar com senha temporária"}
                  </button>
                </form>
              )}

              <div className="grid gap-4 sm:grid-cols-3">
                <Metric label="Usuários cadastrados" value={String(usuarios.length)} />
                <Metric label="Usuários ativos" value={String(usuarios.filter((item) => item.ativo).length)} />
                <Metric label="Primeiro acesso pendente" value={String(usuarios.filter((item) => item.status_acesso === "PRIMEIRO_ACESSO_PENDENTE").length)} />
              </div>

              <section className="overflow-hidden rounded-3xl border border-[#13203f] bg-[#071427]">
                <div className="border-b border-[#13203f] px-6 py-5"><h2 className="text-lg font-bold">Contas reais cadastradas</h2></div>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-[#061326] text-xs uppercase text-slate-500"><tr><th className="px-6 py-4">Usuário</th><th className="px-6 py-4">Função</th><th className="px-6 py-4">Território / DDDs</th><th className="px-6 py-4">Situação</th></tr></thead>
                    <tbody className="divide-y divide-[#13203f]">
                      {usuarios.map((item) => (
                        <tr key={item.id}>
                          <td className="px-6 py-4"><strong>{item.nome}</strong><div className="mt-1 text-xs text-slate-500">{item.email}</div></td>
                          <td className="px-6 py-4 text-cyan-300">{item.tipo_usuario}</td>
                          <td className="px-6 py-4 text-slate-300">{item.territorio || "—"}{item.ddds?.length ? ` / ${item.ddds.join(", ")}` : ""}</td>
                          <td className="px-6 py-4"><span className="rounded-full border border-[#254b75] px-3 py-1 text-xs text-slate-300">{item.status_acesso || (item.ativo ? "ATIVO" : "INATIVO")}</span></td>
                        </tr>
                      ))}
                      {usuarios.length === 0 && <tr><td colSpan={4} className="px-6 py-10 text-center text-slate-500">Nenhuma conta real cadastrada.</td></tr>}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#071427] p-5"><div className="text-xs uppercase text-slate-500">{label}</div><div className="mt-2 text-2xl font-bold text-cyan-300">{value}</div></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">{children}</div> }
function Campo({ label, value, onChange, placeholder, type = "text", required = false }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string; required?: boolean }) { return <label className="text-sm text-slate-300">{label}<input value={value} type={type} required={required} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3" /></label> }
function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: { valor: string; rotulo: string }[] }) { return <label className="text-sm text-slate-300">{label}<select value={value} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3">{options.map((item) => <option key={item.valor} value={item.valor}>{item.rotulo}</option>)}</select></label> }
