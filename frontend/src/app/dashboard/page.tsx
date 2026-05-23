"use client"

import { useMemo, useState } from "react"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

import { KPICard } from "@/components/dashboard/KPICard"
import { RevenueChart } from "@/components/dashboard/RevenueChart"

import ImplementadorasTable from "@/modules/implementadoras/components/ImplementadorasTable"
import ImplementadoraDrawer from "@/modules/implementadoras/components/ImplementadoraDrawer"

import { implementadorasMock } from "@/modules/implementadoras/data/implementadoras.mock"

import { Implementadora } from "@/modules/implementadoras/types/implementadora.types"

import TerritorialMap from "@/components/dashboard/TerritorialMap"

export default function Home() {
  /*
   * DRAWER
   */

  const [drawerOpen, setDrawerOpen] =
    useState(false)

  const [
    selectedImplementadora,
    setSelectedImplementadora,
  ] =
    useState<Implementadora | null>(
      null
    )

  function handleOpenDrawer(
    implementadora: Implementadora
  ) {
    setSelectedImplementadora(
      implementadora
    )

    setDrawerOpen(true)
  }

  function handleCloseDrawer() {
    setDrawerOpen(false)
  }

  /*
   * KPIs EXECUTIVOS
   */

  const kpis = useMemo(() => {
    const implementadorasAtivas =
      implementadorasMock.filter(
        (item) =>
          item.status === "Ativo"
      )

    const implementadorasRisco =
      implementadorasMock.filter(
        (item) =>
          item.status ===
            "Inativo" ||
          item.score < 70
      )

    const implementadorasEstrategicas =
      implementadorasMock.filter(
        (item) =>
          item.score >= 85 &&
          (item.marketShare ?? 0) >=
            25
      )

    const oportunidadesTotais =
      implementadorasMock.reduce(
        (acc, item) =>
          acc +
          (item.oportunidadesAbertas ??
            item.oportunidades),
        0
      )

    const scoreMedio =
      Math.round(
        implementadorasMock.reduce(
          (acc, item) =>
            acc + item.score,
          0
        ) /
          implementadorasMock.length
      )

    const crescimentoMedio =
      Math.round(
        implementadorasMock.reduce(
          (acc, item) =>
            acc +
            (item.crescimento ?? 0),
          0
        ) /
          implementadorasMock.length
      )

    return {
      implementadorasAtivas:
        implementadorasAtivas.length,

      implementadorasRisco:
        implementadorasRisco.length,

      implementadorasEstrategicas:
        implementadorasEstrategicas.length,

      oportunidadesTotais,

      scoreMedio,

      crescimentoMedio,
    }
  }, [])

  /*
   * CENTRAL EXECUTIVA IA
   */

  const alertasExecutivos =
    useMemo(() => {
      return [
        {
          tipo: "critico",
          titulo:
            "Thermo King avançando no Sul",

          descricao:
            "Monitoramento identificou aumento competitivo em operações refrigeradas estratégicas.",

          badge: "ALERTA CONCORRENCIAL",
        },

        {
          tipo: "monitoramento",
          titulo:
            "Facchini em observação operacional",

          descricao:
            "IA detectou desaceleração regional e necessidade de fortalecimento comercial.",

          badge: "MONITORAMENTO IA",
        },

        {
          tipo: "positivo",
          titulo:
            "Carrier expandindo em Santa Catarina",

          descricao:
            "Crescimento operacional acelerado em implementadoras estratégicas da região Sul.",

          badge: "EXPANSÃO CARRIER",
        },

        {
          tipo: "estrategico",
          titulo:
            "Randon elevada para prioridade máxima",

          descricao:
            "Implementadora tornou-se foco prioritário da inteligência operacional do CTI.",

          badge: "PRIORIDADE EXECUTIVA",
        },
      ]
    }, [])

  /*
   * CORES DOS ALERTAS
   */

  function getAlertStyle(
    tipo: string
  ) {
    switch (tipo) {
      case "critico":
        return {
          border:
            "border-red-500/20",

          bg:
            "from-red-500/10 to-red-500/5",

          badge:
            "bg-red-500/10 text-red-400 border-red-500/20",

          icon: "🔴",
        }

      case "monitoramento":
        return {
          border:
            "border-yellow-500/20",

          bg:
            "from-yellow-500/10 to-yellow-500/5",

          badge:
            "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",

          icon: "🟡",
        }

      case "positivo":
        return {
          border:
            "border-emerald-500/20",

          bg:
            "from-emerald-500/10 to-emerald-500/5",

          badge:
            "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",

          icon: "🟢",
        }

      default:
        return {
          border:
            "border-cyan-500/20",

          bg:
            "from-cyan-500/10 to-cyan-500/5",

          badge:
            "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",

          icon: "🔵",
        }
    }
  }

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />

      <section className="flex-1 min-w-0 overflow-hidden">
        <Topbar />

        <div className="p-8 w-full max-w-full overflow-hidden">
          {/* HERO */}

          <div className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                <span className="text-cyan-400 text-2xl">
                  ✦
                </span>
              </div>

              <div>
                <h1 className="text-2xl font-bold text-white">
                  HUB CENTRAL CTI
                </h1>

                <p className="text-cyan-400 mt-1 text-sm">
                  Central operacional de
                  inteligência comercial
                </p>
              </div>
            </div>

            <p className="text-gray-400 text-base max-w-2xl leading-relaxed">
              Plataforma executiva de
              inteligência operacional,
              análise territorial,
              monitoramento concorrencial
              e expansão estratégica
              Carrier.
            </p>
          </div>

          {/* KPI GRID */}

          <div className="grid grid-cols-1 xl:grid-cols-4 md:grid-cols-2 gap-4 mb-8">
            <KPICard
              title="Implementadoras Estratégicas"
              value={String(
                kpis.implementadorasEstrategicas
              )}
              change={`${kpis.scoreMedio}% score médio`}
            />

            <KPICard
              title="Operações em Risco"
              value={String(
                kpis.implementadorasRisco
              )}
              change="Monitoramento IA"
              positive={false}
            />

            <KPICard
              title="Expansão Carrier"
              value={`${kpis.crescimentoMedio}%`}
              change="Crescimento operacional"
            />

            <KPICard
              title="Oportunidades Ativas"
              value={String(
                kpis.oportunidadesTotais
              )}
              change={`${kpis.implementadorasAtivas} implementadoras ativas`}
            />
          </div>

          {/* CENTRAL EXECUTIVA IA */}

          <div className="mb-8">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-3xl font-bold text-white">
                  Central Executiva IA
                </h2>

                <p className="text-gray-400 mt-1 text-sm">
                  Alertas estratégicos e
                  inteligência operacional
                  em tempo real
                </p>
              </div>

              <div className="px-4 py-2 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs">
                IA OPERACIONAL ATIVA
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              {alertasExecutivos.map(
                (alerta, index) => {
                  const style =
                    getAlertStyle(
                      alerta.tipo
                    )

                  return (
                    <div
                      key={index}
                      className={`
                        bg-gradient-to-br
                        ${style.bg}
                        border
                        ${style.border}
                        rounded-2xl
                        p-4
                      `}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">
                            {
                              style.icon
                            }
                          </span>

                          <span
                            className={`
                              px-3 py-1 rounded-xl text-[11px] font-semibold border
                              ${style.badge}
                            `}
                          >
                            {
                              alerta.badge
                            }
                          </span>
                        </div>
                      </div>

                      <h3 className="text-xl font-bold text-white leading-tight">
                        {
                          alerta.titulo
                        }
                      </h3>

                      <p className="text-gray-400 mt-3 text-sm leading-relaxed">
                        {
                          alerta.descricao
                        }
                      </p>
                    </div>
                  )
                }
              )}
            </div>
          </div>

          {/* GRÁFICO EXECUTIVO */}

          <RevenueChart />

          {/* MAPA TERRITORIAL */}

          <div className="mt-8">
            <TerritorialMap />
          </div>

          {/* TABELA */}

          <div className="mt-8">
           <div className="mt-8 bg-[#091a33] border border-[#13203f] rounded-2xl p-6">
             <div className="flex items-center justify-between">
               <div>
                 <p className="text-cyan-400 text-sm font-medium">
                   IMPLEMENTADORAS
                 </p>

                 <h3 className="text-2xl font-bold text-white mt-2">
                   Inteligência Operacional
                 </h3>

                 <p className="text-gray-400 mt-3 max-w-2xl">
                   Monitoramento estratégico de implementadoras,
                   concorrência regional, expansão Carrier
                   e oportunidades comerciais.
                 </p>
              </div>

              <button className="px-6 py-3 rounded-xl bg-cyan-500 text-black font-semibold hover:bg-cyan-400 transition">
                Abrir Módulo
              </button>
            </div>

            <div className="grid grid-cols-4 gap-4 mt-6">
              <div className="bg-[#071226] rounded-xl p-4 border border-[#13203f]">
                <p className="text-gray-400 text-sm">
                  Estratégicas
                </p>

                <p className="text-cyan-400 text-3xl font-bold mt-2">
                  2
                </p>
              </div>

              <div className="bg-[#071226] rounded-xl p-4 border border-[#13203f]">
                <p className="text-gray-400 text-sm">
                  Expansão
                </p>

                <p className="text-emerald-400 text-3xl font-bold mt-2">
                  5
                </p>
              </div>

              <div className="bg-[#071226] rounded-xl p-4 border border-[#13203f]">
                <p className="text-gray-400 text-sm">
                  Concorrência
                </p>

                <p className="text-orange-400 text-3xl font-bold mt-2">
                  1
                </p>
              </div>

              <div className="bg-[#071226] rounded-xl p-4 border border-[#13203f]">
                <p className="text-gray-400 text-sm">
                  Score Médio
                </p>

                <p className="text-white text-3xl font-bold mt-2">
                  82%
                </p>
              </div>
            </div>
          </div>
          </div>

          {/* DRAWER */}

          <ImplementadoraDrawer
            implementadora={
              selectedImplementadora
            }
            open={drawerOpen}
            onClose={
              handleCloseDrawer
            }
          />
        </div>
      </section>
    </main>
  )
}