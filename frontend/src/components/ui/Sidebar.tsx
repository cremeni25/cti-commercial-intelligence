"use client"

import Image from "next/image"
import logoCTI from "@/assets/logo/Logo CTI - fundo azul.png"
import Link from "next/link"
import { usePathname } from "next/navigation"

import trailerIcon from "@/assets/equipamentos/trailer.png"
import dieselTruckIcon from "@/assets/equipamentos/diesel-truck.png"
import directDriveIcon from "@/assets/equipamentos/direct-drive.png"

const perfilAtual = "ADMIN_MASTER"

const permissoesMenu = {
  ADMIN_MASTER: [
    "/dashboard",
    "/ia-comercial",
    "/transportadoras",
    "/implementadoras",
    "/locadoras",
    "/oportunidades",
    "/pipeline",
    "/propostas",
    "/pedidos",
    "/atividades",
    "/forecast",
    "/mapa-estrategico",
    "/equipamentos/trailer",
    "/equipamentos/diesel-truck",
    "/equipamentos/direct-drive",
    "/configuracoes",
    "/usuarios",
  ],

  DIRETOR: [
    "/dashboard",
    "/ia-comercial",
    "/transportadoras",
    "/implementadoras",
    "/locadoras",
    "/oportunidades",
    "/pipeline",
    "/propostas",
    "/pedidos",
    "/atividades",
    "/forecast",
    "/mapa-estrategico",
    "/equipamentos/trailer",
    "/equipamentos/diesel-truck",
    "/equipamentos/direct-drive",
    "/configuracoes",
    "/usuarios",
  ],

  GERENTE: [
    "/dashboard",
    "/transportadoras",
    "/implementadoras",
    "/locadoras",
    "/oportunidades",
  ],

  VENDEDOR: [
    "/dashboard",
    "/oportunidades",
  ],
}

const menuGroups = [
  {
    titulo: "",
    itens: [
      {
        label: "Dashboard Executivo",
        href: "/dashboard",
        icon: "📊",
        type: "emoji",
      },
      {
        label: "IA Comercial",
        href: "/ia-comercial",
        icon: "🧠",
        type: "emoji",
      },
    ],
  },

  {
    titulo: "CRM",
    itens: [
      {
        label: "Oportunidades",
        href: "/oportunidades",
        icon: "📈",
        type: "emoji",
      },
      {
        label: "Pipeline",
        href: "/pipeline",
        icon: "🔄",
        type: "emoji",
      },
      {
        label: "Propostas",
        href: "/propostas",
        icon: "📄",
        type: "emoji",
      },
      {
        label: "Pedidos",
        href: "/pedidos",
        icon: "📦",
        type: "emoji",
      },
      {
        label: "Atividades",
        href: "/atividades",
        icon: "📅",
        type: "emoji",
      },
      {
        label: "Forecast",
        href: "/forecast",
        icon: "📊",
        type: "emoji",
      },
    ],
  },

  {
    titulo: "Cadastros",
    itens: [
      {
        label: "Transportadoras",
        href: "/transportadoras",
        icon: "🚛",
        type: "emoji",
      },
      {
        label: "Implementadoras",
        href: "/implementadoras",
        icon: "🏭",
        type: "emoji",
      },
      {
        label: "Locadoras",
        href: "/locadoras",
        icon: "🏢",
        type: "emoji",
      },
    ],
  },

  {
    titulo: "Equipamentos",
    itens: [
      {
        label: "TR • Trailer",
        href: "/equipamentos/trailer",
        icon: trailerIcon,
        type: "image",
      },
      {
        label: "DT • Diesel Truck",
        href: "/equipamentos/diesel-truck",
        icon: dieselTruckIcon,
        type: "image",
      },
      {
        label: "DD • Direct Drive",
        href: "/equipamentos/direct-drive",
        icon: directDriveIcon,
        type: "image",
      },
    ],
  },

  {
    titulo: "",
    itens: [
      {
        label: "Mapa Estratégico",
        href: "/mapa-estrategico",
        icon: "🌎",
        type: "emoji",
      },
    ],
  },

  {
    titulo: "Administração",
    itens: [
      {
        label: "Usuários",
        href: "/usuarios",
        icon: "👥",
        type: "emoji",
      },
      {
        label: "Configurações",
        href: "/configuracoes",
        icon: "⚙️",
        type: "emoji",
      },
    ],
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  const menusPermitidos =
    permissoesMenu[
      perfilAtual as keyof typeof permissoesMenu
    ] || []

  return (
    <aside className="w-[300px] min-h-screen bg-[#071028] border-r border-[#13203f] flex flex-col">
      {/* HEADER */}
      <div className="p-4 border-b border-[#13203f] flex justify-center">
        <Image
          src={logoCTI}
          alt="CTI"
          width={220}
          height={90}
          priority
          className="object-contain"
        />
      </div>

      {/* MENU */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">

      {menuGroups.map((grupo, index) => (
        <div key={`${grupo.titulo}-${index}`}>

      {grupo.titulo && (
        <p className="px-4 pt-4 pb-2 text-xs uppercase tracking-widest text-[#6c8ecf]">
          {grupo.titulo}
        </p>
      )}

      {grupo.itens
        .filter((item) =>
          menusPermitidos.includes(item.href)
        )
        .map((item) => {
          const active = pathname === item.href

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                w-full flex items-center gap-3 rounded-xl px-4 py-3 transition-all
                ${
                  active
                    ? "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400"
                    : "text-gray-300 hover:bg-[#101b36]"
                }
              `}
            >
              <div className="w-[28px] flex items-center justify-center">

                {item.type === "image" ? (
                  <Image
                    src={item.icon as any}
                    alt={item.label}
                    width={28}
                    height={28}
                    className="object-contain"
                  />
                ) : (
                  <span className="text-lg">
                    {item.icon as string}
                  </span>
                )}

              </div>

              <span>{item.label}</span>

            </Link>
          )
        })}
    </div>
  ))}

</nav>

      {/* FOOTER */}
      <div className="p-4 border-t border-[#13203f]">
        <div className="bg-[#101b36] rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-widest">
            Status Sistema
          </p>

          <div className="flex items-center gap-2 mt-3">
            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />

            <span className="text-green-400 text-sm font-medium">
              Online
            </span>
          </div>
        </div>
      </div>
    </aside>
  )
}