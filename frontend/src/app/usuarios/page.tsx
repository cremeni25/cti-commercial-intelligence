/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import {
  aprovarSolicitacao,
  criarUsuario,
  listarSolicitacoes,
  listarUsuarios,
  rejeitarSolicitacao,
  type DecisaoSolicitacao,
  type PerfilCTI,
  type SolicitacaoAcesso,
  type UsuarioNovo,
} from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI } from "@/modules/usuarios/types/usuario.types"

const perfis: PerfilCTI[] = ["DIRETOR", "GESTOR_REGIONAL", "VENDEDOR_REGIONAL", "GERENTE", "VENDEDOR"]
const decisaoInicial: DecisaoSolicitacao = { tipo_usuario: "VENDEDOR_REGIONAL", territorio: "", ddds: [], acesso_portal: true, acesso_crm: true }
const usuarioInicial: UsuarioNovo = { nome: "", email: "", senha: "", empresa: "Viena São Paulo", cargo: "", tipo_usuario: "VENDEDOR_REGIONAL", territorio: "", ddds: [], superior_id: undefined }

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [usuarios, setUsuarios] = useState<UsuarioCTI[]>([])
  const [solicitacoes, setSolicitacoes] = useState<SolicitacaoAcesso[]>([])
  const [selecionada, setSelecionada] = useState<SolicitacaoAcesso | null>(null)
  const [decisao, setDecisao] = useState<DecisaoSolicitacao>(decisaoInicial)
  const [dddsTexto, setDddsTexto] = useState("")
  const [motivo, setMotivo] = useState("")
  const [novo, setNovo] = useState<UsuarioNovo>(usuarioInicial)
  const [novoDdds, setNovoDdds] = useState("")
  const [mostrarNovo, setMostrarNovo] = useState(false)
  const [loading, setLoading] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")

  const autorizado = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"

  async function carregar() {
    setLoading(true); setErro("")
    try {
      const [contas, pedidos] = await Promise.all([listarUsuarios(), listarSolicitacoes()])
      setUsuarios(contas); setSolicitacoes(pedidos)
    } catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível carregar a governança de usuários.") }
    finally { setLoading(false) }
  }

  useEffect(() => { if (authLoading) return; if (!autorizado) return setLoading(false); void carregar() }, [authLoading, autorizado])

  const pendentes = useMemo(() => solicitacoes.filter((item) => item.status === "PENDENTE"), [solicitacoes])
  const superiores = usuarios.filter((item) => item.ativo && ["ADMIN_MASTER", "DIRETOR", "GESTOR_REGIONAL", "GERENTE"].includes(String(item.tipo_usuario)))

  function limparAvisos() { setErro(""); setMensagem("") }
  function abrir(item: SolicitacaoAcesso) {
    setSelecionada(item); setDecisao({ ...decisaoInicial, acesso_portal: item.canal_solicitado !== "CRM", acesso_crm: item.canal_solicitado !== "PORTAL" })
    setDddsTexto(""); setMotivo(""); limparAvisos()
  }

  async function cadastrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setProcessando(true); limparAvisos()
    try {
      await criarUsuario({ ...novo, email: novo.email.trim().toLowerCase(), ddds: novoDdds.split(",").map((item) => item.trim()).filter(Boolean), superior_id: novo.superior_id || undefined })
      setMensagem("Usuário criado, confirmado e liberado para Portal CTI e App CRM.")
      setNovo(usuarioInicial); setNovoDdds(""); setMostrarNovo(false); await carregar()
    } catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível criar o usuário.") }
    finally { setProcessando(false) }
  }

  async function aprovar() {
    if (!selecionada) return
    setProcessando(true); limparAvisos()
    try {
      await aprovarSolicitacao(selecionada.id, { ...decisao, ddds: dddsTexto.split(",").map((item) => item.trim()).filter(Boolean), superior_id: decisao.superior_id || undefined, motivo_decisao: motivo || undefined })
      setMensagem("Solicitação aprovada e convite seguro enviado."); setSelecionada(null); await carregar()
    } catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível aprovar a solicitação.") }
    finally { setProcessando(false) }
  }

  async function rejeitar() {
    if (!selecionada || motivo.trim().length < 3) return setErro("Informe o motivo da rejeição.")
    setProcessando(true); limparAvisos()
    try { await rejeitarSolicitacao(selecionada.id, motivo.trim()); setMensagem("Solicitação rejeitada e registrada."); setSelecionada(null); await carregar() }
    catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível rejeitar a solicitação.") }
    finally { setProcessando(false) }
  }

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6 lg:p-8"><p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">CTI Administração</p><div className="mt-3 flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div><h1 className="text-3xl font-bold">Governança de usuários e acessos</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">Criação direta, solicitações, perfis, hierarquia, territórios e DDDs para o Portal e o App CRM.</p></div>{autorizado && <button type="button" onClick={() => { setMostrarNovo(!mostrarNovo); limparAvisos() }} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">{mostrarNovo ? "Fechar cadastro" : "Criar usuário"}</button>}</div></header>

    {authLoading || loading ? <Aviso>Carregando solicitações e contas...</Aviso> : !autorizado ? <Aviso>Este módulo é exclusivo do ADMIN_MASTER.</Aviso> : <>
      {mensagem && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/30 px-5 py-4 text-sm text-emerald-200">{mensagem}</div>}
      {erro && <div className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</div>}

      {mostrarNovo && <form onSubmit={cadastrar} className="rounded-3xl border border-cyan-900 bg-[#071427] p-5 sm:p-6"><h2 className="text-xl font-bold">Novo usuário CTI</h2><p className="mt-1 text-sm text-slate-400">A conta será criada confirmada e ativa nos dois ambientes.</p><div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Campo label="Nome completo" value={novo.nome} onChange={(value) => setNovo({ ...novo, nome: value })} required />
        <Campo label="E-mail" type="email" value={novo.email} onChange={(value) => setNovo({ ...novo, email: value })} required />
        <Campo label="Senha inicial" type="password" value={novo.senha} onChange={(value) => setNovo({ ...novo, senha: value })} placeholder="Mínimo 8 caracteres" required />
        <Campo label="Empresa" value={novo.empresa} onChange={(value) => setNovo({ ...novo, empresa: value })} required />
        <Campo label="Cargo" value={novo.cargo} onChange={(value) => setNovo({ ...novo, cargo: value })} required />
        <Select label="Perfil" value={novo.tipo_usuario} onChange={(value) => setNovo({ ...novo, tipo_usuario: value as PerfilCTI })} options={perfis} />
        <Campo label="Território" value={novo.territorio || ""} onChange={(value) => setNovo({ ...novo, territorio: value })} />
        <Campo label="DDDs autorizados" value={novoDdds} onChange={setNovoDdds} placeholder="011, 012, 013" />
        <label className="text-sm text-slate-300">Superior hierárquico<select value={novo.superior_id || ""} onChange={(e) => setNovo({ ...novo, superior_id: e.target.value || undefined })} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3"><option value="">Sem superior definido</option>{superiores.map((item) => <option key={item.id} value={item.id}>{item.nome} — {item.tipo_usuario}</option>)}</select></label>
      </div><button disabled={processando} className="mt-5 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60">{processando ? "Criando..." : "Criar e ativar usuário"}</button></form>}

      <div className="grid gap-4 sm:grid-cols-3"><Metric label="Solicitações pendentes" value={String(pendentes.length)} /><Metric label="Usuários cadastrados" value={String(usuarios.length)} /><Metric label="Usuários ativos" value={String(usuarios.filter((item) => item.ativo).length)} /></div>

      <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><h2 className="text-xl font-bold">Solicitações de acesso</h2><p className="mt-1 text-sm text-slate-400">O ADMIN_MASTER define escopo e envia o convite.</p><div className="mt-5 grid gap-3 lg:grid-cols-2">{pendentes.length === 0 ? <p className="text-sm text-slate-500">Nenhuma solicitação pendente.</p> : pendentes.map((item) => <button key={item.id} onClick={() => abrir(item)} className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4 text-left hover:border-cyan-700"><div className="flex items-start justify-between gap-3"><strong>{item.nome}</strong><span className="rounded-full border border-amber-800 px-2 py-1 text-[10px] text-amber-300">PENDENTE</span></div><p className="mt-1 text-xs text-slate-400">{item.email}</p><p className="mt-3 text-sm text-slate-300">{item.empresa} — {item.cargo}</p><p className="mt-1 text-xs text-cyan-300">Solicitado: {item.canal_solicitado}</p></button>)}</div></section>

      {selecionada && <section className="rounded-3xl border border-cyan-900 bg-[#071427] p-5 sm:p-6"><h2 className="text-xl font-bold">Analisar: {selecionada.nome}</h2><div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3"><Select label="Perfil" value={decisao.tipo_usuario} onChange={(value) => setDecisao({ ...decisao, tipo_usuario: value as PerfilCTI })} options={perfis} /><Campo label="Território" value={decisao.territorio || ""} onChange={(value) => setDecisao({ ...decisao, territorio: value })} /><Campo label="DDDs autorizados" value={dddsTexto} onChange={setDddsTexto} placeholder="011, 012, 013" /><label className="text-sm text-slate-300">Superior hierárquico<select value={decisao.superior_id || ""} onChange={(e) => setDecisao({ ...decisao, superior_id: e.target.value || undefined })} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3"><option value="">Sem superior definido</option>{superiores.map((item) => <option key={item.id} value={item.id}>{item.nome} — {item.tipo_usuario}</option>)}</select></label><label className="flex items-center gap-3 rounded-xl border border-[#1d3b67] p-4 text-sm"><input type="checkbox" checked={decisao.acesso_portal} onChange={(e) => setDecisao({ ...decisao, acesso_portal: e.target.checked })} /> Portal CTI</label><label className="flex items-center gap-3 rounded-xl border border-[#1d3b67] p-4 text-sm"><input type="checkbox" checked={decisao.acesso_crm} onChange={(e) => setDecisao({ ...decisao, acesso_crm: e.target.checked })} /> App CRM</label><label className="text-sm text-slate-300 md:col-span-2 xl:col-span-3">Observação da decisão<textarea value={motivo} onChange={(e) => setMotivo(e.target.value)} className="mt-2 min-h-24 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3" /></label></div><div className="mt-5 flex flex-wrap gap-3"><button disabled={processando} onClick={aprovar} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60">Aprovar e enviar convite</button><button disabled={processando} onClick={rejeitar} className="rounded-xl border border-red-800 px-5 py-3 font-semibold text-red-300 disabled:opacity-60">Rejeitar solicitação</button><button onClick={() => setSelecionada(null)} className="px-4 py-3 text-sm text-slate-400">Cancelar</button></div></section>}

      <section className="overflow-hidden rounded-3xl border border-[#13203f] bg-[#071427]"><div className="border-b border-[#13203f] px-6 py-5"><h2 className="text-lg font-bold">Contas cadastradas</h2></div><div className="overflow-x-auto"><table className="min-w-full text-left text-sm"><thead className="bg-[#061326] text-xs uppercase text-slate-500"><tr><th className="px-6 py-4">Usuário</th><th className="px-6 py-4">Perfil</th><th className="px-6 py-4">Empresa</th><th className="px-6 py-4">Território / DDDs</th><th className="px-6 py-4">Situação</th></tr></thead><tbody className="divide-y divide-[#13203f]">{usuarios.map((item) => <tr key={item.id}><td className="px-6 py-4"><strong>{item.nome}</strong><div className="text-xs text-slate-500">{item.email}</div></td><td className="px-6 py-4 text-cyan-300">{item.tipo_usuario}</td><td className="px-6 py-4 text-slate-300">{item.empresa || "—"}</td><td className="px-6 py-4 text-slate-300">{String(item.territorio || "—")}<div className="text-xs text-slate-500">{Array.isArray(item.ddds) ? item.ddds.join(", ") : ""}</div></td><td className="px-6 py-4">{item.ativo ? "ATIVO" : "INATIVO"}</td></tr>)}</tbody></table></div></section>
    </>}
  </div></section></main>
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#071427] p-5"><div className="text-xs uppercase text-slate-500">{label}</div><div className="mt-2 text-2xl font-bold text-cyan-300">{value}</div></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">{children}</div> }
function Campo({ label, value, onChange, placeholder, type = "text", required = false }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string; required?: boolean }) { return <label className="text-sm text-slate-300">{label}<input value={value} type={type} required={required} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3" /></label> }
function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) { return <label className="text-sm text-slate-300">{label}<select value={value} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3">{options.map((item) => <option key={item}>{item}</option>)}</select></label> }
