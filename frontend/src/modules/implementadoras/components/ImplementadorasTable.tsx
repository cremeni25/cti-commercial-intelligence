"use client"

import { Implementadora } from "../types/implementadora.types"

import {
  ordenarImplementadoras,
  getRankingBadge,
  getScoreColor,
  gerarInsights,
} from "../services/implementadoras.engine"

interface Props {
  implementadoras: Implementadora[]

  onSelectImplementadora: (
    implementadora: Implementadora
  ) => void
}

export default function ImplementadorasTable({
  implementadoras,
  onSelectImplementadora,
}: Props) {
  /*
   * ENGINE OPERACIONAL
   */

  const implementadorasOrdenadas =
    ordenarImplementadoras(
      implementadoras
    )

  return (
    <div className="w-full max-w-full bg-[#071226] border border-[#13203f] rounded-3xl p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-4xl font-bold text-white">
            Ranking Executivo CTI
          </h2>

          <p className="text-gray-400 mt-3 text-lg">
            Inteligência operacional,
            expansão Carrier e
            monitoramento territorial
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-4 py-2 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm">
            IA Operacional
          </div>

          <div className="px-4 py-2 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
            Enterprise
          </div>
        </div>
      </div>

      <div className="w-full overflow-x-auto rounded-3xl border border-[#13203f]">
        <table className="w-full min-w-[1200px] xl:min-w-[1400px]">
          <thead className="bg-[#091a33]">
            <tr className="text-left">
              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Ranking
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Implementadora
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Criticidade IA
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Região
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Market Share
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Crescimento
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Score Operacional
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Score Comercial
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Temperatura
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Equipamentos
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Oportunidades
              </th>

              <th className="px-6 py-5 text-sm font-semibold text-gray-300">
                Status
              </th>
            </tr>
          </thead>

          <tbody>
            {implementadorasOrdenadas.map(
              (
                implementadora,
                index
              ) => {
                const insights =
                  gerarInsights(
                    implementadora
                  )

                return (
                  <tr
                    key={
                      implementadora.id
                    }
                    onClick={() =>
                      onSelectImplementadora(
                        implementadora
                      )
                    }
                    className="
                      border-t border-[#13203f]
                      hover:bg-[#0b1d39]
                      transition-all
                      cursor-pointer
                    "
                  >
                    <td className="px-6 py-6">
                      <div className="flex flex-col gap-2">
                        <span className="text-3xl font-bold text-cyan-400">
                          #
                          {index + 1}
                        </span>

                        <span className="text-xs text-gray-400">
                          {getRankingBadge(
                            index
                          )}
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <div>
                        <p className="text-white font-bold text-lg">
                          {
                            implementadora.nome
                          }
                        </p>

                        <p className="text-sm text-gray-400 mt-2">
                          {
                            implementadora.cidade
                          }{" "}
                          -{" "}
                          {
                            implementadora.estado
                          }
                        </p>

                        <div className="mt-3 flex flex-wrap gap-2">
                          {implementadora.ddds?.map(
                            (
                              ddd
                            ) => (
                              <span
                                key={
                                  ddd
                                }
                                className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs"
                              >
                                {ddd}
                              </span>
                            )
                          )}
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <div className="space-y-3">
                        <span
                          className={`
                            px-4 py-2 rounded-2xl text-xs font-semibold inline-flex

                            ${
                              insights.criticidade ===
                              "PRIORIDADE MÁXIMA"
                                ? "bg-red-500/10 border border-red-500/20 text-red-400"

                                : insights.criticidade ===
                                  "MONITORAMENTO"
                                ? "bg-yellow-500/10 border border-yellow-500/20 text-yellow-400"

                                : "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400"
                            }
                          `}
                        >
                          {
                            insights.criticidade
                          }
                        </span>

                        <div className="text-sm text-gray-400">
                          {
                            insights.badgeExecutiva
                          }
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <div>
                        <p className="text-cyan-400 font-bold text-lg">
                          {
                            implementadora.regiao
                          }
                        </p>

                        <p className="text-gray-400 text-sm mt-2">
                          Dominância{" "}
                          {
                            implementadora.dominanciaRegional
                          }
                        </p>
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <div>
                        <p className="text-white font-bold text-2xl">
                          {
                            implementadora.marketShare
                          }
                          %
                        </p>

                        <p className="text-gray-400 text-sm mt-2">
                          Participação regional
                        </p>
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <div>
                        <p className="text-emerald-400 font-bold text-2xl">
                          +
                          {
                            implementadora.crescimento
                          }
                          %
                        </p>

                        <p className="text-gray-400 text-sm mt-2">
                          Expansão operacional
                        </p>
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <div>
                        <p
                          className={`
                            text-3xl font-bold

                            ${getScoreColor(
                              implementadora.scoreOperacional ??
                                implementadora.score
                            )}
                          `}
                        >
                          {
                            implementadora.scoreOperacional ??
                            implementadora.score
                          }
                          %
                        </p>

                        <div className="mt-3 h-2 rounded-full bg-[#11203a] overflow-hidden w-[140px]">
                          <div
                            className="h-2 rounded-full bg-gradient-to-r from-cyan-400 to-cyan-300"
                            style={{
                              width: `${
                                implementadora.scoreOperacional ??
                                implementadora.score
                              }%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <p className="text-emerald-400 font-bold text-3xl">
                        {
                          implementadora.scoreComercial ??
                          implementadora.score
                        }
                        %
                      </p>
                    </td>

                    <td className="px-6 py-6">
                      <span className="text-sm text-white">
                        {
                          insights.temperaturaOperacional
                        }
                      </span>
                    </td>

                    <td className="px-6 py-6">
                      <div className="flex flex-wrap gap-2 max-w-[260px]">
                        {(
                          implementadora.equipamentosRelacionados ??
                          implementadora.equipamentos
                        )?.map(
                          (
                            equipamento
                          ) => (
                            <span
                              key={
                                equipamento
                              }
                              className={`
                                px-3 py-1 rounded-full text-xs border

                                ${
                                  equipamento ===
                                  "CARRIER"
                                    ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-400"
                                    : "bg-[#11203a] border-[#1b315f] text-white"
                                }
                              `}
                            >
                              {
                                equipamento
                              }
                            </span>
                          )
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-6">
                      <p className="text-cyan-400 font-bold text-3xl">
                        {
                          implementadora.oportunidadesAbertas ??
                          implementadora.oportunidades
                        }
                      </p>
                    </td>

                    <td className="px-6 py-6">
                      <span
                        className={`
                          px-4 py-2 rounded-2xl text-xs font-semibold

                          ${
                            implementadora.status ===
                            "Ativo"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"

                              : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }
                        `}
                      >
                        {
                          implementadora.status
                        }
                      </span>
                    </td>
                  </tr>
                )
              }
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}