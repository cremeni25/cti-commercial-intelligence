"use client"

import { useState } from "react"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts"

export function RevenueChart() {
  const [dashboard] = useState<{ clientes?: unknown[]; implementadoras?: unknown[]; estados?: Array<[string, number]>; produtos?: Array<[string, number]>; resumo?: { total_registros?: number } } | null>(null)
  const [data] = useState<Array<{ mes: string; oportunidades: number }>>([])
  return (
    <div className="bg-[#071226] border border-[#13203f] rounded-2xl p-6 mb-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">
            Inteligência Operacional
          </h2>

          <p className="text-gray-400 mt-2">
            Evolução comercial e performance territorial
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-4 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
            <p className="text-xs text-gray-400 uppercase">
              ÍNDICE GLOBAL CTI
            </p>

            <p className="text-xl font-bold text-cyan-400">
              {dashboard?.clientes?.length ?? 0}
            </p>
          </div>

          <div className="px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <p className="text-xs text-gray-400 uppercase">
              Crescimento
            </p>

            <p className="text-xl font-bold text-emerald-400">
              {dashboard?.implementadoras?.length ?? 0}
            </p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <AreaChart
          width={1400}
          height={420}
          data={data}
        >
          <defs>
            <linearGradient
              id="colorOportunidades"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="5%"
                stopColor="#06b6d4"
                stopOpacity={0.4}
              />

              <stop
                offset="95%"
                stopColor="#06b6d4"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#11203a"
          />

          <XAxis
            dataKey="mes"
            stroke="#6b7280"
            tickLine={false}
            axisLine={false}
          />

          <YAxis
            stroke="#6b7280"
            tickLine={false}
            axisLine={false}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: "#071226",
              border: "1px solid #13203f",
              borderRadius: "16px",
              color: "#fff",
            }}
          />

          <Area
            type="monotone"
            dataKey="oportunidades"
            stroke="#06b6d4"
            strokeWidth={4}
            fillOpacity={1}
            fill="url(#colorOportunidades)"
          />
        </AreaChart>
      </div>

      <div className="grid grid-cols-4 gap-4 mt-8">
        <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
          <p className="text-sm text-gray-400">
            Melhor Região
          </p>

          <p className="text-2xl font-bold text-cyan-400 mt-2">
            {dashboard?.estados?.[0]?.[0] ?? "-"}
          </p>
        </div>

        <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
          <p className="text-sm text-gray-400">
            DDD Dominante
          </p>

          <p className="text-2xl font-bold text-cyan-400 mt-2">
            {dashboard?.clientes?.length ?? 0}
          </p>
        </div>

        <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
          <p className="text-sm text-gray-400">
            Top Performance
          </p>

          <p className="text-2xl font-bold text-emerald-400 mt-2">
            {dashboard?.implementadoras?.length ?? 0}
          </p>
        </div>

        <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
          <p className="text-sm text-gray-400">
            Oportunidades
          </p>

          <p className="text-2xl font-bold text-cyan-400 mt-2">
            {dashboard?.resumo?.total_registros ?? 0}
          </p>
        </div>
      </div>
    </div>
  )
}