"use client"

import Image, { type StaticImageData } from "next/image"
import logoCTI from "@/assets/logo/Logo CTI - fundo azul.png"
import Link from "next/link"
import { usePathname } from "next/navigation"

import trailerIcon from "@/assets/equipamentos/trailer.png"
import dieselTruckIcon from "@/assets/equipamentos/diesel-truck.png"
import directDriveIcon from "@/assets/equipamentos/direct-drive.png"
import { useAuth } from "@/core/auth/AuthContext"
import type { PermissoesSessaoCTI } from "@/core/auth/types"
import { useI18n, type MessageKey } from "@/core/i18n"
import LanguageSwitcher from "@/components/i18n/LanguageSwitcher"

type LocalizedLabel = { "pt-BR": string; en: string; es: string }
type MenuItem = { labelKey?: MessageKey; label?: LocalizedLabel; href: string; icon: string | StaticImageData; type: "emoji" | "image" }
type MenuGroup = { tituloKey: MessageKey; itens: MenuItem[] }

const menuGroups: MenuGroup[] = [
  {
    tituloKey: "nav.main",
    itens: [
      { labelKey: "nav.dashboard", href: "/dashboard", icon: "📊", type: "emoji" },
      { labelKey: "nav.history", href: "/historico-comercial", icon: "🗂️", type: "emoji" },
      { labelKey: "nav.salesAi", href: "/ia-comercial", icon: "🧠", type: "emoji" },
    ],
  },
  {
    tituloKey: "nav.crm",
    itens: [
      { labelKey: "nav.opportunities", href: "/oportunidades", icon: "📈", type: "emoji" },
      { labelKey: "nav.pipeline", href: "/pipeline", icon: "🔄", type: "emoji" },
      { labelKey: "nav.import", href: "/upload", icon: "📤", type: "emoji" },
      { labelKey: "nav.proposals", href: "/propostas", icon: "📄", type: "emoji" },
      { labelKey: "nav.orders", href: "/pedidos", icon: "📦", type: "emoji" },
      { labelKey: "nav.sales", href: "/vendas", icon: "💰", type: "emoji" },
      { labelKey: "nav.reports", href: "/relatorios", icon: "📑", type: "emoji" },
      { labelKey: "nav.generateReport", href: "/relatorios/modular", icon: "🖨️", type: "emoji" },
      { labelKey: "nav.activities", href: "/atividades", icon: "📅", type: "emoji" },
      { labelKey: "nav.forecast", href: "/forecast", icon: "📊", type: "emoji" },
    ],
  },
  {
    tituloKey: "nav.masterData",
    itens: [
      { labelKey: "nav.companies", href: "/empresas", icon: "🏢", type: "emoji" },
      { labelKey: "nav.bodyBuilders", href: "/implementadoras", icon: "🏭", type: "emoji" },
    ],
  },
  {
    tituloKey: "nav.equipment",
    itens: [
      { labelKey: "nav.trailer", href: "/equipamentos/trailer", icon: trailerIcon, type: "image" },
      { labelKey: "nav.dieselTruck", href: "/equipamentos/diesel-truck", icon: dieselTruckIcon, type: "image" },
      { labelKey: "nav.directDrive", href: "/equipamentos/direct-drive", icon: directDriveIcon, type: "image" },
      { labelKey: "nav.strategicMap", href: "/mapa-estrategico", icon: "🌎", type: "emoji" },
    ],
  },
  {
    tituloKey: "nav.administration",
    itens: [
      { labelKey: "nav.sourceGovernance", href: "/backoffice-fontes", icon: "🗄️", type: "emoji" },
      { labelKey: "nav.users", href: "/usuarios", icon: "👥", type: "emoji" },
      { labelKey: "nav.settings", href: "/configuracoes", icon: "⚙️", type: "emoji" },
      { labelKey: "nav.officialTemplates", href: "/configuracoes/modelos-oficiais", icon: "📑", type: "emoji" },
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
  if (href === "/dashboard" || href === "/inteligencia") return gestao || tem(permissoes, "dashboard_executivo")
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
  const { t, locale } = useI18n()
  const perfil = String(usuario?.tipo_usuario || "").toUpperCase()
  const permissoes = usuario?.permissoes
  const acessoTotal = Boolean(usuario?.acesso_total || permissoes?.acesso_total)

  return (
    <aside className="w-[300px] min-h-screen bg-[#071028] border-r border-[#13203f] flex flex-col">
      <div className="p-4 border-b border-[#13203f] flex flex-col items-center gap-3">
        <Image src={logoCTI} alt="CTI" width={220} height={90} priority className="object-contain" />
        <LanguageSwitcher compact />
      </div>

      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {menuGroups.map((grupo, index) => {
          const itensPermitidos = grupo.itens.filter((item) => rotaPermitida(item.href, perfil, permissoes, acessoTotal))
          if (itensPermitidos.length === 0) return null
          return (
            <div key={`${grupo.tituloKey}-${index}`}>
              <p className="px-4 pt-4 pb-2 text-xs uppercase tracking-widest text-[#6c8ecf]">{t(grupo.tituloKey)}</p>
              {itensPermitidos.map((item) => {
                const active = pathname === item.href
                const label = item.labelKey ? t(item.labelKey) : item.label?.[locale] || item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`w-full flex items-center gap-3 rounded-xl px-4 py-3 transition-all ${active ? "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400" : "text-gray-300 hover:bg-[#101b36]"}`}
                  >
                    <div className="w-[28px] flex items-center justify-center">
                      {item.type === "image" ? (
                        <Image src={item.icon as StaticImageData} alt={label} width={28} height={28} className="object-contain" />
                      ) : (
                        <span className="text-lg">{item.icon as string}</span>
                      )}
                    </div>
                    <span>{label}</span>
                  </Link>
                )
              })}
            </div>
          )
        })}
      </nav>

      <div className="p-4 border-t border-[#13203f]">
        <div className="bg-[#101b36] rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-widest">{t("common.systemStatus")}</p>
          <div className="flex items-center gap-2 mt-3">
            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
            <span className="text-green-400 text-sm font-medium">{t("common.online")}</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
