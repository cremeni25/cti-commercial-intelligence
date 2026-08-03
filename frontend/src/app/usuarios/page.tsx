/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import {
  alterarEstadoUsuario,
  atualizarUsuario,
  criarUsuario,
  excluirUsuario,
  listarUsuarios,
  type PermissoesUsuario,
  type UsuarioAtualizacao,
  type UsuarioNovo,
} from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI } from "@/modules/usuarios/types/usuario.types"

const permissoesIniciais: PermissoesUsuario = {
  acesso_portal: true,
  acesso_crm: true,
  dashboard_executivo: false,
  clientes_visualizar: true,
  clientes_editar: false,
  oportunidades_visualizar: true,
  oportunidades_editar: true,
  propostas_visualizar: true,
  propostas_emitir: false,
  pedidos_visualizar: true,
  pedidos_converter: false,
  pedidos_enviar: false,
  financeiro_visualizar: false,
  usuarios_administrar: false,
  configuracoes_administrar: false,
  acesso_total: false,
}

const usuarioInicial: UsuarioNovo = {
  nome: "",
  email: "",
  senha_temporaria: "",
  empresa: "VIENA SP",
  funcao: "",
  territorio: "Viena SP",
  ddds: [],
  gestor_responsavel: "",
  permissoes: permissoesIniciais,
}

const grupos: { titulo: string; itens: { chave: keyof PermissoesUsuario; rotulo: string }[] }[] = [
  { titulo: "Canais", itens: [
    { chave: "acesso_portal", rotulo: "Acessar o site" },
    { chave: "acesso_crm", rotulo: "Acessar o CRM App" },
    { chave: "dashboard_executivo", rotulo: "Dashboard executivo" },
  ]},
  { titulo: "Operação comercial", itens: [
    { chave: "clientes_visualizar", rotulo: "Visualizar clientes" },
    { chave: "clientes_editar", rotulo: "Criar e editar clientes" },
    { chave: "oportunidades_visualizar", rotulo: "Visualizar oportunidades" },
    { chave: "oportunidades_editar", rotulo: "Criar e editar oportunidades" },
    { chave: "propostas_visualizar", rotulo: "Visualizar propostas" },
    { chave: "propostas_emitir", rotulo: "Emitir propostas" },
    { chave: "pedidos_visualizar", rotulo: "Visualizar pedidos" },
    { chave: "pedidos_converter", rotulo: "Converter proposta em pedido" },
    { chave: "pedidos_enviar", rotulo: "Enviar pedidos" },
  ]},
  { titulo: "Administração", itens: [
    { chave: "financeiro_visualizar", rotulo: "Visualizar valores financeiros" },
    { chave: "usuarios_administrar", rotulo: "Administrar usuários" },
    { chave: "configuracoes_administrar", rotulo: "Administrar configurações" },
    { chave: "acesso_total", rotulo: "Acesso total" },
  ]},
]

function permissoesCompletas(item?: Partial<PermissoesUsuario>): PermissoesUsuario {
  return { ...permissoesIniciais, ...item }
}

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [usuarios, setUsuarios] = useState<UsuarioCTI[]>([])
  const [novo, setNovo] = useState<UsuarioNovo>(usuarioInicial)
  const [dddsTexto, setDddsTexto] = useState("")
  const [mostrarNovo, setMostrarNovo] = useState(false)
  const [editando, setEditando] = useState<UsuarioCTI | null>(null)
  const [edicao, setEdicao] = useState<UsuarioAtualizacao | null>(null)
  const [dddsEdicao, setDddsEdicao] = useState("")
  const [excluindo, setExcluindo] = useState<UsuarioCTI | null>(null)
  const [confirmacaoEmail, setConfirmacaoEmail] = useState("")
  const [loading, setLoading] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const autorizado = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"

  async function carregar() {
    setLoading(true)
    setErro("")
    try { setUsuarios(await listarUsuarios()) }
    catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível carregar os usuários.") }
    finally { setLoading(false) }
  }

  useEffect(() => {
    if (authLoading) return
    if (!autorizado) return setLoading(false)
    void carregar()
  }, [authLoading, autorizado])

  function marcarNovo(chave: keyof PermissoesUsuario, valor: boolean) {
    const permissoes = { ...novo.permissoes, [chave]: valor }
    if (chave === "acesso_total" && valor) Object.keys(permissoes).forEach((item) => { permissoes[item as keyof PermissoesUsuario] = true })
    setNovo({ ...novo, permissoes })
  }

  function marcarEdicao(chave: keyof PermissoesUsuario, valor: boolean) {
    if (!edicao) return
    const permissoes = { ...edicao.permissoes, [chave]: valor }
    if (chave === "acesso_total" && valor) Object.keys(permissoes).forEach((item) => { permissoes[item as keyof PermissoesUsuario] = true })
    setEdicao({ ...edicao, permissoes })
  }

  async function cadastrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setProcessando(true); setErro(""); setMensagem("")
    try {
      await criarUsuario({ ...novo, email: novo.email.trim().toLowerCase(), gestor_responsavel: novo.gestor_responsavel?.trim() || null, ddds: dddsTexto.split(",").map((item) => item.trim()).filter(Boolean) })
      setMensagem("Usuário criado. A senha deverá ser substituída no primeiro acesso.")
      setNovo(usuarioInicial); setDddsTexto(""); setMostrarNovo(false)
      await carregar()
    } catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível criar o usuário.") }
    finally { setProcessando(false) }
  }

  function abrirEdicao(item: UsuarioCTI) {
    setEditando(item)
    setDddsEdicao((item.ddds || []).join(", "))
    setEdicao({
      nome: item.nome,
      empresa: item.empresa || "VIENA SP",
      funcao: item.funcao || item.cargo || "",
      territorio: item.territorio || "",
      ddds: item.ddds || [],
      gestor_responsavel: item.gestor_responsavel || "",
      permissoes: permissoesCompletas(item.permissoes),
    })
    setErro(""); setMensagem("")
  }

  async function salvarEdicao(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!editando || !edicao) return
    setProcessando(true); setErro(""); setMensagem("")
    try {
      await atualizarUsuario(editando.id, { ...edicao, gestor_responsavel: edicao.gestor_responsavel?.trim() || null, ddds: dddsEdicao.split(",").map((item) => item.trim()).filter(Boolean) })
      setMensagem("Dados e permissões atualizados.")
      setEditando(null); setEdicao(null)
      await carregar()
    } catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível atualizar o usuário.") }
    finally { setProcessando(false) }
  }

  async function alternarEstado(item: UsuarioCTI) {
    const acao = item.ativo ? "desativar" : "reativar"
    if (!window.confirm(`Confirma ${acao} o acesso de ${item.nome}?`)) return
    setProcessando(true); setErro(""); setMensagem("")
    try {
      await alterarEstadoUsuario(item.id, !item.ativo)
      setMensagem(item.ativo ? "Usuário desativado. O histórico comercial foi preservado." : "Usuário reativado.")
      await carregar()
    } catch (error) { setErro(error instanceof Error ? error.message : `Não foi possível ${acao} o usuário.`) }
    finally { setProcessando(false) }
  }

  async function confirmarExclusao() {
    if (!excluindo) return
    setProcessando(true); setErro(""); setMensagem("")
    try {
      await excluirUsuario(excluindo.id, confirmacaoEmail.trim().toLowerCase())
      setMensagem("Usuário excluído definitivamente.")
      setExcluindo(null); setConfirmacaoEmail("")
      await carregar()
    } catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível excluir o usuário.") }
    finally { setProcessando(false) }
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
              <div><h1 className="text-3xl font-bold">Usuários e permissões</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">Cadastre, edite, desative ou exclua contas criadas por engano. A desativação preserva todo o histórico comercial.</p></div>
              {autorizado && <button type="button" onClick={() => setMostrarNovo(!mostrarNovo)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">{mostrarNovo ? "Fechar cadastro" : "Criar usuário"}</button>}
            </div>
          </header>

          {authLoading || loading ? <Aviso>Carregando usuários...</Aviso> : !autorizado ? <Aviso>Este módulo é exclusivo do Admin Master.</Aviso> : <>
            {mensagem && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/30 px-5 py-4 text-sm text-emerald-200">{mensagem}</div>}
            {erro && <div className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</div>}

            {mostrarNovo && <UsuarioForm titulo="Novo usuário CTI" subtitulo="Função livre, gestor livre e permissões individuais." dados={novo} dddsTexto={dddsTexto} setDddsTexto={setDddsTexto} onChange={setNovo} onMarcar={marcarNovo} onSubmit={cadastrar} processando={processando} botao="Criar usuário e aplicar permissões" incluirCredenciais />}

            {editando && edicao && <UsuarioForm titulo={`Editar ${editando.nome}`} subtitulo={`E-mail de autenticação: ${editando.email}`} dados={edicao} dddsTexto={dddsEdicao} setDddsTexto={setDddsEdicao} onChange={setEdicao} onMarcar={marcarEdicao} onSubmit={salvarEdicao} processando={processando} botao="Salvar dados e permissões" onCancelar={() => { setEditando(null); setEdicao(null) }} />}

            {excluindo && <section className="rounded-3xl border border-red-800 bg-red-950/20 p-6"><h2 className="text-xl font-bold text-red-200">Excluir definitivamente</h2><p className="mt-2 text-sm text-red-200/80">Disponível apenas enquanto o primeiro acesso não foi concluído. Para confirmar, digite o e-mail <strong>{excluindo.email}</strong>.</p><div className="mt-4 flex flex-col gap-3 sm:flex-row"><input value={confirmacaoEmail} onChange={(e) => setConfirmacaoEmail(e.target.value)} className="flex-1 rounded-xl border border-red-700 bg-[#061126] px-4 py-3" placeholder="Digite o e-mail completo" /><button disabled={processando || confirmacaoEmail.trim().toLowerCase() !== excluindo.email.toLowerCase()} onClick={() => void confirmarExclusao()} className="rounded-xl bg-red-600 px-5 py-3 font-semibold disabled:opacity-40">Excluir conta</button><button onClick={() => { setExcluindo(null); setConfirmacaoEmail("") }} className="rounded-xl border border-slate-600 px-5 py-3">Cancelar</button></div></section>}

            <div className="grid gap-4 sm:grid-cols-3"><Metric label="Usuários cadastrados" value={String(usuarios.length)} /><Metric label="Usuários ativos" value={String(usuarios.filter((item) => item.ativo).length)} /><Metric label="Primeiro acesso pendente" value={String(usuarios.filter((item) => item.status_acesso === "PRIMEIRO_ACESSO_PENDENTE").length)} /></div>

            <section className="overflow-hidden rounded-3xl border border-[#13203f] bg-[#071427]"><div className="border-b border-[#13203f] px-6 py-5"><h2 className="text-lg font-bold">Contas reais cadastradas</h2></div><div className="overflow-x-auto"><table className="min-w-full text-left text-sm"><thead className="bg-[#061326] text-xs uppercase text-slate-500"><tr><th className="px-6 py-4">Usuário</th><th className="px-6 py-4">Cargo / função</th><th className="px-6 py-4">Gestor</th><th className="px-6 py-4">Território / DDDs</th><th className="px-6 py-4">Acessos</th><th className="px-6 py-4">Situação</th><th className="px-6 py-4">Ações</th></tr></thead><tbody className="divide-y divide-[#13203f]">{usuarios.map((item) => { const protegido = String(item.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"; return <tr key={item.id}><td className="px-6 py-4"><strong>{item.nome}</strong><div className="mt-1 text-xs text-slate-500">{item.email}</div></td><td className="px-6 py-4 text-cyan-300">{item.funcao || item.cargo || "—"}</td><td className="px-6 py-4 text-slate-300">{item.gestor_responsavel || "—"}</td><td className="px-6 py-4 text-slate-300">{item.territorio || "—"}{item.ddds?.length ? ` / ${item.ddds.join(", ")}` : ""}</td><td className="px-6 py-4 text-xs text-slate-300">{item.permissoes?.acesso_total ? "ACESSO TOTAL" : [item.permissoes?.acesso_portal && "SITE", item.permissoes?.acesso_crm && "CRM"].filter(Boolean).join(" + ") || "SEM ACESSO"}</td><td className="px-6 py-4"><span className="rounded-full border border-[#254b75] px-3 py-1 text-xs text-slate-300">{item.status_acesso || (item.ativo ? "ATIVO" : "INATIVO")}</span></td><td className="px-6 py-4"><div className="flex flex-wrap gap-2"><button onClick={() => abrirEdicao(item)} className="rounded-lg border border-cyan-800 px-3 py-2 text-xs text-cyan-200">Editar</button>{!protegido && <button disabled={processando} onClick={() => void alternarEstado(item)} className="rounded-lg border border-amber-700 px-3 py-2 text-xs text-amber-200">{item.ativo ? "Desativar" : "Reativar"}</button>}{!protegido && item.primeiro_acesso_pendente && !item.cadastro_completo && <button onClick={() => { setExcluindo(item); setConfirmacaoEmail("") }} className="rounded-lg border border-red-800 px-3 py-2 text-xs text-red-200">Excluir</button>}</div></td></tr> })}</tbody></table></div></section>
          </>}
        </div>
      </section>
    </main>
  )
}

function UsuarioForm({ titulo, subtitulo, dados, dddsTexto, setDddsTexto, onChange, onMarcar, onSubmit, processando, botao, incluirCredenciais = false, onCancelar }: { titulo: string; subtitulo: string; dados: UsuarioNovo | UsuarioAtualizacao; dddsTexto: string; setDddsTexto: (v: string) => void; onChange: (v: any) => void; onMarcar: (k: keyof PermissoesUsuario, v: boolean) => void; onSubmit: (e: FormEvent<HTMLFormElement>) => void; processando: boolean; botao: string; incluirCredenciais?: boolean; onCancelar?: () => void }) {
  return <form onSubmit={onSubmit} className="space-y-6 rounded-3xl border border-cyan-900 bg-[#071427] p-5 sm:p-6"><div><h2 className="text-xl font-bold">{titulo}</h2><p className="mt-1 text-sm text-slate-400">{subtitulo}</p></div><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"><Campo label="Nome completo" value={dados.nome} onChange={(value) => onChange({ ...dados, nome: value })} required />{incluirCredenciais && "email" in dados && <><Campo label="E-mail" type="email" value={dados.email} onChange={(value) => onChange({ ...dados, email: value })} required /><Campo label="Senha temporária" type="password" value={dados.senha_temporaria} onChange={(value) => onChange({ ...dados, senha_temporaria: value })} required /></>}<Campo label="Cargo ou função" value={dados.funcao} onChange={(value) => onChange({ ...dados, funcao: value })} required /><Campo label="Empresa" value={dados.empresa} onChange={(value) => onChange({ ...dados, empresa: value })} required /><Campo label="Território" value={dados.territorio || ""} onChange={(value) => onChange({ ...dados, territorio: value })} /><Campo label="DDDs autorizados" value={dddsTexto} onChange={setDddsTexto} placeholder="011, 012, 013" /><Campo label="Gestor responsável" value={dados.gestor_responsavel || ""} onChange={(value) => onChange({ ...dados, gestor_responsavel: value })} /></div><div className="grid gap-4 lg:grid-cols-3">{grupos.map((grupo) => <fieldset key={grupo.titulo} className="rounded-2xl border border-[#17345e] bg-[#061126] p-4"><legend className="px-2 font-semibold text-cyan-300">{grupo.titulo}</legend><div className="space-y-3">{grupo.itens.map((item) => <label key={item.chave} className="flex items-center gap-3 text-sm text-slate-200"><input type="checkbox" checked={dados.permissoes[item.chave]} onChange={(e) => onMarcar(item.chave, e.target.checked)} className="h-4 w-4 accent-cyan-500" />{item.rotulo}</label>)}</div></fieldset>)}</div><div className="flex flex-wrap gap-3"><button disabled={processando} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60">{processando ? "Processando..." : botao}</button>{onCancelar && <button type="button" onClick={onCancelar} className="rounded-xl border border-slate-600 px-5 py-3">Cancelar</button>}</div></form>
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#071427] p-5"><div className="text-xs uppercase text-slate-500">{label}</div><div className="mt-2 text-2xl font-bold text-cyan-300">{value}</div></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">{children}</div> }
function Campo({ label, value, onChange, placeholder, type = "text", required = false }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string; required?: boolean }) { return <label className="text-sm text-slate-300">{label}<input value={value} type={type} required={required} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3" /></label> }
