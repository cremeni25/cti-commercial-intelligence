"use client"

import Image, { type StaticImageData } from "next/image"
import logoCTI from "@/assets/logo/Logo CTI - fundo azul.png"
import Link from "next/link"
import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"

import trailerIcon from "@/assets/equipamentos/trailer.png"
import dieselTruckIcon from "@/assets/equipamentos/diesel-truck.png"
import directDriveIcon from "@/assets/equipamentos/direct-drive.png"
import { useAuth } from "@/core/auth/AuthContext"
import type { PermissoesSessaoCTI } from "@/core/auth/types"
import { useI18n, type MessageKey } from "@/core/i18n"
import LanguageSwitcher from "@/components/i18n/LanguageSwitcher"

type LocalizedLabel = { "pt-BR": string; en: string; es: string }
type MenuItem = { labelKey?: MessageKey; label?: LocalizedLabel; href: string; icon: string | StaticImageData; type: "emoji" | "image"; aliases?: string[] }
type MenuGroup = { tituloKey?: MessageKey; titulo?: LocalizedLabel; itens: MenuItem[] }

const menuGroups: MenuGroup[] = [
  { titulo: { "pt-BR": "Leitura Estratégica", en: "Strategic Intelligence", es: "Lectura Estratégica" }, itens: [
    { label: { "pt-BR": "Mapa Estratégico", en: "Strategic Map", es: "Mapa Estratégico" }, href: "/mapa-estrategico", aliases: ["/inteligencia-comercial"], icon: "◎", type: "emoji" },
    { labelKey: "nav.salesAi", href: "/ia-comercial", icon: "🧠", type: "emoji" },
  ]},
  { tituloKey: "nav.crm", itens: [
    { label: { "pt-BR": "Nova interação", en: "New interaction", es: "Nueva interacción" }, href: "/atividades/interacao", icon: "✚", type: "emoji" },
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
  ]},
  { tituloKey: "nav.masterData", itens: [
    { labelKey: "nav.companies", href: "/empresas", icon: "🏢", type: "emoji" },
    { label: { "pt-BR": "Carteiras Comerciais", en: "Customer Portfolios", es: "Carteras Comerciales" }, href: "/dashboard/carteiras-comerciais", icon: "🗂️", type: "emoji" },
    { labelKey: "nav.bodyBuilders", href: "/implementadoras", icon: "🏭", type: "emoji" },
  ]},
  { tituloKey: "nav.equipment", itens: [
    { labelKey: "nav.trailer", href: "/equipamentos/trailer", icon: trailerIcon, type: "image" },
    { labelKey: "nav.dieselTruck", href: "/equipamentos/diesel-truck", icon: dieselTruckIcon, type: "image" },
    { labelKey: "nav.directDrive", href: "/equipamentos/direct-drive", icon: directDriveIcon, type: "image" },
  ]},
  { tituloKey: "nav.administration", itens: [
    { label: { "pt-BR": "Inteligência de Mercado", en: "Market Intelligence", es: "Inteligencia de Mercado" }, href: "/inteligencia", icon: "📊", type: "emoji" },
    { labelKey: "nav.sourceGovernance", href: "/backoffice-fontes", icon: "🗄️", type: "emoji" },
    { labelKey: "nav.users", href: "/usuarios", icon: "👥", type: "emoji" },
    { labelKey: "nav.settings", href: "/configuracoes", icon: "⚙️", type: "emoji" },
    { labelKey: "nav.officialTemplates", href: "/configuracoes/modelos-oficiais", icon: "📑", type: "emoji" },
  ]},
]

function tem(permissoes: PermissoesSessaoCTI | undefined, chave: keyof PermissoesSessaoCTI) { return permissoes?.[chave] === true }

function rotaPermitida(href: string, perfil: string, permissoes: PermissoesSessaoCTI | undefined, acessoTotal: boolean) {
  const master = perfil === "ADMIN_MASTER"
  const diretor = perfil === "DIRETOR_VIENA_SP"
  const gestao = master || (diretor && acessoTotal)
  if (href === "/backoffice-fontes" || href === "/configuracoes/modelos-oficiais" || href === "/inteligencia") return master
  if (href === "/usuarios") return master || tem(permissoes, "usuarios_administrar")
  if (href === "/configuracoes") return master || tem(permissoes, "configuracoes_administrar")
  if (href === "/upload") return gestao
  if (href === "/dashboard" || href === "/inteligencia-comercial") return gestao || tem(permissoes, "dashboard_executivo") || tem(permissoes, "oportunidades_visualizar")
  if (href === "/empresas" || href === "/dashboard/carteiras-comerciais" || href === "/implementadoras") return gestao || tem(permissoes, "clientes_visualizar")
  if (href === "/atividades/interacao") return gestao || tem(permissoes, "oportunidades_visualizar") || tem(permissoes, "oportunidades_editar")
  if (href === "/oportunidades" || href === "/pipeline" || href === "/historico-comercial" || href === "/ia-comercial" || href === "/atividades" || href === "/forecast" || href === "/mapa-estrategico") return gestao || tem(permissoes, "oportunidades_visualizar")
  if (href === "/propostas") return gestao || tem(permissoes, "propostas_visualizar")
  if (href === "/pedidos") return gestao || tem(permissoes, "pedidos_visualizar")
  if (href === "/vendas" || href === "/relatorios" || href === "/relatorios/modular") return gestao || tem(permissoes, "dashboard_executivo")
  if (href.startsWith("/equipamentos/")) return gestao || tem(permissoes, "oportunidades_visualizar")
  return master
}

export default function Sidebar() {
  const pathname = usePathname(); const { usuario } = useAuth(); const { t, locale } = useI18n()
  const [menuMobileAberto, setMenuMobileAberto] = useState(false)
  useEffect(() => { setMenuMobileAberto(false) }, [pathname])
  const perfil = String(usuario?.tipo_usuario || "").toUpperCase(); const permissoes = usuario?.permissoes; const acessoTotal = Boolean(usuario?.acesso_total || permissoes?.acesso_total)
  return <><button type="button" onClick={() => setMenuMobileAberto(true)} aria-label="Abrir menu de navegação" aria-expanded={menuMobileAberto} className="fixed left-3 top-3 z-40 rounded-xl border border-[#CBD5E1] bg-white px-4 py-3 text-sm font-bold text-[#0F172A] shadow-lg lg:hidden">☰ Menu</button>
    {menuMobileAberto && <button type="button" aria-label="Fechar menu de navegação" onClick={() => setMenuMobileAberto(false)} className="fixed inset-0 z-40 bg-black/60 lg:hidden" />}
    <aside className={`fixed inset-y-0 left-0 z-50 flex w-[min(85vw,320px)] flex-col overflow-y-auto border-r border-[#2B435C] bg-[#14283F] transition-transform duration-200 lg:static lg:z-auto lg:min-h-screen lg:w-[300px] lg:shrink-0 lg:translate-x-0 ${menuMobileAberto ? "translate-x-0" : "-translate-x-full"}`}>
    <button type="button" onClick={() => setMenuMobileAberto(false)} aria-label="Fechar menu" className="absolute right-3 top-3 rounded-lg border border-[#2B435C] px-3 py-2 text-white lg:hidden">✕</button>
    <div className="p-4 border-b border-[#2B435C] flex flex-col items-center gap-3"><Image src={logoCTI} alt="CTI" width={220} height={90} priority className="object-contain"/><LanguageSwitcher compact/></div>
    <nav className="flex-1 p-4 space-y-2 overflow-y-auto">{menuGroups.map((grupo,index)=>{const itensPermitidos=grupo.itens.filter(item=>rotaPermitida(item.href,perfil,permissoes,acessoTotal));if(itensPermitidos.length===0)return null;const tituloGrupo=grupo.tituloKey?t(grupo.tituloKey):grupo.titulo?.[locale]||"";return <div key={`${grupo.tituloKey||tituloGrupo}-${index}`}><p className="px-4 pt-4 pb-2 text-xs uppercase tracking-widest text-[#B6D2EB]">{tituloGrupo}</p>{itensPermitidos.map(item=>{const active=pathname===item.href||Boolean(item.aliases?.some(alias=>pathname===alias||pathname.startsWith(`${alias}/`)));const label=item.labelKey?t(item.labelKey):item.label?.[locale]||item.href;return <Link key={item.href} href={item.href} className={`w-full flex items-center gap-3 rounded-xl px-4 py-3 transition-all ${active?"bg-[#D6EEFA] border border-[#8CCDEB] text-[#0F3554]":"text-slate-200 hover:bg-[#243E58]"}`}><div className="w-[28px] flex items-center justify-center">{item.type==="image"?<Image src={item.icon as StaticImageData} alt={label} width={28} height={28} className="object-contain"/>:<span className="text-lg">{item.icon as string}</span>}</div><span>{label}</span></Link>})}</div>})}</nav>
    <div className="p-4 border-t border-[#2B435C]"><div className="bg-[#243E58] rounded-xl p-4"><p className="text-xs text-gray-400 uppercase tracking-widest">{t("common.systemStatus")}</p><div className="flex items-center gap-2 mt-3"><div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"/><span className="text-green-400 text-sm font-medium">{t("common.online")}</span></div></div></div>
  </aside></>
}
