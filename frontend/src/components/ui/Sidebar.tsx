"use client"

import Image, { type StaticImageData } from "next/image"
import logoCTI from "@/assets/logo/Logo CTI - sem fundo.png"
import logoViena from "@/assets/logo/Logo Viena - transparente.png"
import Link from "next/link"
import { usePathname } from "next/navigation"

import trailerIcon from "@/assets/equipamentos/trailer.png"
import dieselTruckIcon from "@/assets/equipamentos/diesel-truck.png"
import directDriveIcon from "@/assets/equipamentos/direct-drive.png"
import { useAuth } from "@/core/auth/AuthContext"
import type { PermissoesSessaoCTI } from "@/core/auth/types"

type MenuItem = { label: string; href: string; icon: string | StaticImageData; type: "emoji" | "image" }
type MenuGroup = { titulo: string; itens: MenuItem[] }

const menuGroups: MenuGroup[] = [
  {
    titulo: "Principal",
    itens: [
      { label: "Dashboard Executivo", href: "/dashboard", icon: "📊", type: "emoji" },
      { label: "Histórico Comercial", href: "/historico-comercial", icon: "🗂️", type: "emoji" },
      { label: "IA Comercial", href: "/ia-comercial", icon: "🧠", type: "emoji" },
    ],
  },
  {
    titulo: "CRM",
    itens: [
      { label: "Oportunidades", href: "/oportunidades", icon: "📈", type: "emoji" },
      { label: "Pipeline", href: "/pipeline", icon: "🔄", type: "emoji" },
      { label: "Importar Dados", href: "/upload", icon: "📤", type: "emoji" },
      { label: "Propostas", href: "/propostas", icon: "📄", type: "emoji" },
      { label: "Pedidos", href: "/pedidos", icon: "📦", type: "emoji" },
      { label: "Vendas", href: "/vendas", icon: "💰", type: "emoji" },
      { label: "Relatórios", href: "/relatorios", icon: "📑", type: "emoji" },
      { label: "Gerar relatório", href: "/relatorios/modular", icon: "🖨️", type: "emoji" },
      { label: "Atividades", href: "/atividades", icon: "📅", type: "emoji" },
      { label: "Forecast", href: "/forecast", icon: "📊", type: "emoji" },
    ],
  },
  {
    titulo: "Cadastros",
    itens: [
      { label: "Empresas", href: "/empresas", icon: "🏢", type: "emoji" },
      { label: "Implementadoras", href: "/implementadoras", icon: "🏭", type: "emoji" },
    ],
  },
  {
    titulo: "Equipamentos",
    itens: [
      { label: "TR • Trailer", href: "/equipamentos/trailer", icon: trailerIcon, type: "image" },
      { label: "DT • Diesel Truck", href: "/equipamentos/diesel-truck", icon: dieselTruckIcon, type: "image" },
      { label: "DD • Direct Drive", href: "/equipamentos/direct-drive", icon: directDriveIcon, type: "image" },
      { label: "Mapa Estratégico", href: "/mapa-estrategico", icon: "🌎", type: "emoji" },
    ],
  },
  {
    titulo: "Administração",
    itens: [
      { label: "Governança de Fontes", href: "/backoffice-fontes", icon: "🗄️", type: "emoji" },
      { label: "Usuários", href: "/usuarios", icon: "👥", type: "emoji" },
      { label: "Configurações", href: "/configuracoes", icon: "⚙️", type: "emoji" },
      { label: "Modelos oficiais", href: "/configuracoes/modelos-oficiais", icon: "📑", type: "emoji" },
    ],
  },
]

function tem(permissoes: PermissoesSessaoCTI | undefined, chave: keyof PermissoesSessaoCTI) {
  return permissoes?.[chave] === true
}

function rotaPermitida(href: string, perfil: string, permissoes: PermissoesSessaoCTI | undefined, acessoTotal: boolean) {
  const master = perfil === "ADMIN_MASTER"
  const diretor = perfil === "DIRETOR_VIENA_SP"
  const gestao = master || (diretor && acessoTotal)

  if (href === "/backoffice-fontes" || href === "/configuracoes/modelos-oficiais") return master
  if (href === "/usuarios") return master || tem(permissoes, "usuarios_administrar")
  if (href === "/configuracoes") return master || tem(permissoes, "configuracoes_administrar")
  if (href === "/upload") return gestao
  if (href === "/dashboard") return gestao || tem(permissoes, "dashboard_executivo")
  if (href === "/empresas" || href === "/implementadoras") return gestao || tem(permissoes, "clientes_visualizar")
  if (href === "/oportunidades" || href === "/pipeline" || href === "/historico-comercial" || href === "/ia-comercial" || href === "/atividades" || href === "/forecast" || href === "/mapa-estrategico") return gestao || tem(permissoes, "oportunidades_visualizar")
  if (href === "/propostas") return gestao || tem(permissoes, "propostas_visualizar")
  if (href === "/pedidos") return gestao || tem(permissoes, "pedidos_visualizar")
  if (href === "/vendas" || href === "/relatorios" || href === "/relatorios/modular") return gestao || tem(permissoes, "dashboard_executivo")
  if (href.startsWith("/equipamentos/")) return gestao || tem(permissoes, "oportunidades_visualizar")
  return master
}

export default function Sidebar() {
  const pathname = usePathname()
  const { usuario } = useAuth()
  const perfil = String(usuario?.tipo_usuario || "").toUpperCase()
  const permissoes = usuario?.permissoes
  const acessoTotal = Boolean(usuario?.acesso_total || permissoes?.acesso_total)

  return (
    <aside className="w-[300px] min-h-screen bg-[#071028] border-r border-[#13203f] flex flex-col">
      <div className="border-b border-[#13203f] px-4 pb-4 pt-4">
        <div className="flex flex-col items-center">
          <Image src={logoCTI} alt="CTI — Centro de Tecnologia e Inteligência Comercial" width={230} height={94} priority className="h-auto w-[210px] object-contain" />
          <div className="mt-3 flex w-full items-center gap-3">
            <span className="h-px flex-1 bg-gradient-to-r from-transparent to-[#36567c]" aria-hidden="true" />
            <span className="text-[8px] uppercase tracking-[0.28em] text-slate-500">Operação atendida</span>
            <span className="h-px flex-1 bg-gradient-to-l from-transparent to-[#36567c]" aria-hidden="true" />
          </div>
          <Image src={logoViena} alt="Refrigeração Viena" width={150} height={60} className="mt-2 h-auto w-[118px] object-contain opacity-95" />
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {menuGroups.map((grupo, index) => {
          const itensPermitidos = grupo.itens.filter((item) => rotaPermitida(item.href, perfil, permissoes, acessoTotal))
          if (itensPermitidos.length === 0) return null
          return (
            <div key={`${grupo.titulo}-${index}`}>
              {grupo.titulo && <p className="px-4 pt-4 pb-2 text-xs uppercase tracking-widest text-[#6c8ecf]">{grupo.titulo}</p>}
              {itensPermitidos.map((item) => {
                const active = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`w-full flex items-center gap-3 rounded-xl px-4 py-3 transition-all ${active ? "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400" : "text-gray-300 hover:bg-[#101b36]"}`}
                  >
                    <div className="w-[28px] flex items-center justify-center">
                      {item.type === "image" ? (
                        <Image src={item.icon as StaticImageData} alt={item.label} width={28} height={28} className="object-contain" />
                      ) : (
                        <span className="text-lg">{item.icon as string}</span>
                      )}
                    </div>
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </div>
          )
        })}
      </nav>

      <div className="p-4 border-t border-[#13203f]">
        <div className="bg-[#101b36] rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-widest">Status Sistema</p>
          <div className="flex items-center gap-2 mt-3">
            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
            <span className="text-green-400 text-sm font-medium">Online</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
