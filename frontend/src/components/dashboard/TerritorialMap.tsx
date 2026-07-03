"use client"

import { useEffect, useState } from "react"
import { getDashboardExecutivo } from "@/services/cti-api"

interface EstadoItem {
  estado: string
  quantidade: number
}

interface RegiaoCard {
  regiao: string
  dominancia: string
  temperatura: string
  score: number
  implementadoras: number
  risco: string
  crescimento: string
}

export default function TerritorialMap() {

  const [regioes, setRegioes] = useState<RegiaoCard[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {

    async function carregar() {

      try {

        const dados = await getDashboardExecutivo()

        if (!dados?.estados) {
          setLoading(false)
          return
        }

        const convertidos: RegiaoCard[] =
          dados.estados.map((item: EstadoItem) => {

            const score = Math.min(
              100,
              Number(item.quantidade)
            )

            return {

              regiao: item.estado,

              dominancia:
                score >= 80
                  ? "Alta"
                  : score >= 50
                  ? "Moderada"
                  : "Monitoramento",

              temperatura:
                score >= 80
                  ? "🔥"
                  : score >= 50
                  ? "⚡"
                  : "🟡",

              score,

              implementadoras: item.quantidade,

              risco:
                score >= 80
                  ? "Baixo"
                  : score >= 50
                  ? "Médio"
                  : "Alto",

              crescimento: "--"

            }

          })

        setRegioes(convertidos)

      } catch (error) {

        console.error(
          "Erro ao carregar Analytics Territorial:",
          error
        )

      } finally {

        setLoading(false)

      }

    }

    carregar()

  }, [])

  return (

    <div className="bg-[#091a33] border border-[#13203f] rounded-3xl p-6">

      <div className="flex items-center justify-between mb-8">

        <div>

          <p className="text-gray-400 text-sm uppercase tracking-wide">
            Inteligência Territorial
          </p>

          <h2 className="text-4xl font-bold text-white mt-3">
            Mapa Operacional
          </h2>

        </div>

        <div className="px-4 py-2 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm">
          IA TERRITORIAL
        </div>

      </div>

      {loading ? (

        <div className="text-center text-gray-400 py-20">
          Carregando Inteligência Territorial...
        </div>

      ) : (

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">

          {regioes.map((item) => (

            <div
              key={item.regiao}
              className="bg-[#071226] border border-[#13203f] rounded-3xl p-6"
            >

              <div className="flex items-start justify-between">

                <div>

                  <div className="flex items-center gap-3">

                    <span className="text-3xl">
                      {item.temperatura}
                    </span>

                    <h3 className="text-3xl font-bold text-white">
                      {item.regiao}
                    </h3>

                  </div>

                  <p className="text-gray-400 mt-3">
                    Dominância {item.dominancia}
                  </p>

                </div>

                <div className="text-right">

                  <p className="text-cyan-400 text-4xl font-bold">
                    {item.score}%
                  </p>

                  <p className="text-gray-400 text-sm mt-2">
                    Score regional
                  </p>

                </div>

              </div>

              <div className="mt-6 h-3 rounded-full bg-[#11203a] overflow-hidden">

                <div
                  className="h-3 rounded-full bg-gradient-to-r from-cyan-400 to-cyan-300"
                  style={{
                    width: `${item.score}%`,
                  }}
                />

              </div>

              <div className="grid grid-cols-3 gap-4 mt-6">

                <div>

                  <p className="text-gray-400 text-sm">
                    Implementadoras
                  </p>

                  <p className="text-white text-2xl font-bold mt-2">
                    {item.implementadoras}
                  </p>

                </div>

                <div>

                  <p className="text-gray-400 text-sm">
                    Crescimento
                  </p>

                  <p className="text-emerald-400 text-2xl font-bold mt-2">
                    {item.crescimento}
                  </p>

                </div>

                <div>

                  <p className="text-gray-400 text-sm">
                    Risco
                  </p>

                  <p className="text-red-400 text-2xl font-bold mt-2">
                    {item.risco}
                  </p>

                </div>

              </div>

            </div>

          ))}

        </div>

      )}

    </div>

  )

}