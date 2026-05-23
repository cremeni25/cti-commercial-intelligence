"use client"

import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"

import trailerIcon from "@/assets/equipamentos/trailer.png"
import dieselTruckIcon from "@/assets/equipamentos/diesel-truck.png"
import directDriveIcon from "@/assets/equipamentos/direct-drive.png"

const menuItems = [
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

  {
    label: "Oportunidades",
    href: "/oportunidades",
    icon: "📈",
    type: "emoji",
  },

  {
    label: "Mapa Estratégico",
    href: "/mapa-estrategico",
    icon: "🌎",
    type: "emoji",
  },

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

  {
    label: "Configurações",
    href: "/configuracoes",
    icon: "⚙️",
    type: "emoji",
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-[280px] min-h-screen bg-[#071028] border-r border-[#13203f] flex flex-col">
      {/* HEADER */}
      <div className="p-6 border-b border-[#13203f]">
        <h1 className="text-3xl font-bold text-cyan-400">
          CTI
        </h1>

        <p className="text-sm text-gray-400 mt-2 leading-5">
          Centro de Tecnologia e Inteligência Comercial
        </p>
      </div>

      {/* MENU */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const active =
            pathname === item.href

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
                    src={item.icon}
                    alt={item.label}
                    width={28}
                    height={28}
                    className="object-contain"
                  />
                ) : (
                  <span className="text-lg">
                    {item.icon}
                  </span>
                )}
              </div>

              <span>{item.label}</span>
            </Link>
          )
        })}
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