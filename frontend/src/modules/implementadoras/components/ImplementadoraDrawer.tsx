"use client"

import { X } from "lucide-react"

import { Implementadora } from "../types/implementadora.types"

import {
  gerarInsightsImplementadora,
} from "@/modules/implementadoras/ai/implementadoraInsights"

interface Props {
  implementadora: Implementadora | null
  open: boolean
  onClose: () => void
}

export default function ImplementadoraDrawer({
  implementadora,
  open,
  onClose,
}: Props) {
  if (!implementadora) return null

  /*
   * CONSOLIDAÇÃO DE DADOS
   */

  const scoreOperacional =
    implementadora.scoreOperacional ??
    implementadora.score

  const scoreComercial =
    implementadora.scoreComercial ??
    implementadora.score

  const oportunidades =
    implementadora.oportunidadesAbertas ??
    implementadora.oportunidades

  /*
   * SCORE VISUAL
   */

  function getScoreStyle(score: number) {
    if (score >= 90) {
      return {
        text: "text-cyan-400",
        border: "border-cyan-500/20",
        bg: "from-cyan-500/10 to-cyan-500/5",
        bar: "from-cyan-400 to-cyan-300",
      }
    }

    if (score >= 70) {
      return {
        text: "text-yellow-400",
        border: "border-yellow-500/20",
        bg: "from-yellow-500/10 to-yellow-500/5",
        bar: "from-yellow-400 to-yellow-300",
      }
    }

    return {
      text: "text-red-400",
      border: "border-red-500/20",
      bg: "from-red-500/10 to-red-500/5",
      bar: "from-red-400 to-red-300",
    }
  }

  const scoreOperacionalStyle =
    getScoreStyle(scoreOperacional)

  const scoreComercialStyle =
    getScoreStyle(scoreComercial)

  /*
   * IA CENTRALIZADA
   */

  const insights =
    gerarInsightsImplementadora(
      implementadora
    )

  const alertaIA =
    insights.alertaIA

  const recomendacoesIA =
    insights.recomendacoesIA

  const oportunidadeIA =
    insights.oportunidadeIA

  const riscoConcorrencial =
    insights.riscoConcorrencial

  const prioridadeEstrategica =
    insights.prioridadeEstrategica

  const criticidade =
    insights.criticidade

  const temperaturaOperacional =
    insights.temperaturaOperacional

  const badgeExecutiva =
    insights.badgeExecutiva

  /*
   * BADGES EXECUTIVAS
   */

  const criticidadeColorMap = {
    "PRIORIDADE MÁXIMA":
      "bg-red-500/10 border border-red-500/20 text-red-400",

    MONITORAMENTO:
      "bg-yellow-500/10 border border-yellow-500/20 text-yellow-400",

    "RISCO OPERACIONAL":
      "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400",
  }

  return (
    <>
      <div
        className={`
          fixed inset-0 z-40
          bg-black/70 backdrop-blur-sm
          transition-all duration-300

          ${
            open
              ? "opacity-100"
              : "opacity-0 pointer-events-none"
          }
        `}
        onClick={onClose}
      />

      <aside
        className={`
          fixed top-0 right-0 z-50
          h-screen w-[760px]
          overflow-y-auto

          bg-[#071226]/95
          backdrop-blur-2xl

          border-l border-cyan-500/10

          shadow-[-20px_0_80px_rgba(0,0,0,0.45)]

          transition-all duration-500

          ${
            open
              ? "translate-x-0"
              : "translate-x-full"
          }
        `}
      >
        <div className="sticky top-0 z-30 bg-[#071226]/95 backdrop-blur-xl border-b border-[#13203f]">
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <span
                    className={`
                      px-3 py-1 rounded-full text-xs font-semibold

                      ${
                        implementadora.status === "Ativo"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-red-500/10 text-red-400 border border-red-500/20"
                      }
                    `}
                  >
                    {implementadora.status}
                  </span>

                  <span className="px-3 py-1 rounded-full text-xs bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                    {implementadora.regiao}
                  </span>

                  <span
                    className={`
                      px-4 py-2 rounded-2xl text-xs font-semibold
                      ${
                        criticidadeColorMap[
                          criticidade as keyof typeof criticidadeColorMap
                        ]
                      }
                    `}
                  >
                    {criticidade}
                  </span>

                  <span className="px-4 py-2 rounded-2xl text-xs bg-[#11203a] border border-[#1b315f] text-white">
                    {badgeExecutiva}
                  </span>
                </div>

                <h2 className="text-4xl font-bold text-white">
                  {implementadora.nome}
                </h2>

                <p className="text-gray-400 mt-3 text-lg">
                  Inteligência operacional,
                  territorial e comercial
                </p>

                <p className="text-cyan-400 mt-4 font-medium">
                  {temperaturaOperacional}
                </p>
              </div>

              <button
                onClick={onClose}
                className="w-14 h-14 rounded-2xl bg-[#0b1d39] border border-[#13203f] flex items-center justify-center hover:border-cyan-500/30 hover:bg-[#102547] transition-all"
              >
                <X className="text-white" size={22} />
              </button>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-5">
            <div
              className={`
                bg-gradient-to-br
                ${scoreOperacionalStyle.bg}
                border
                ${scoreOperacionalStyle.border}
                rounded-3xl
                p-6
              `}
            >
              <p className="text-sm text-gray-400 uppercase tracking-wide">
                Score Operacional
              </p>

              <h3
                className={`
                  text-5xl font-bold mt-4
                  ${scoreOperacionalStyle.text}
                `}
              >
                {scoreOperacional}%
              </h3>

              <div className="mt-5 w-full h-3 rounded-full bg-[#11203a] overflow-hidden">
                <div
                  className={`
                    h-3 rounded-full bg-gradient-to-r
                    ${scoreOperacionalStyle.bar}
                  `}
                  style={{
                    width: `${scoreOperacional}%`,
                  }}
                />
              </div>
            </div>

            <div
              className={`
                bg-gradient-to-br
                ${scoreComercialStyle.bg}
                border
                ${scoreComercialStyle.border}
                rounded-3xl
                p-6
              `}
            >
              <p className="text-sm text-gray-400 uppercase tracking-wide">
                Score Comercial
              </p>

              <h3
                className={`
                  text-5xl font-bold mt-4
                  ${scoreComercialStyle.text}
                `}
              >
                {scoreComercial}%
              </h3>

              <div className="mt-5 w-full h-3 rounded-full bg-[#11203a] overflow-hidden">
                <div
                  className={`
                    h-3 rounded-full bg-gradient-to-r
                    ${scoreComercialStyle.bar}
                  `}
                  style={{
                    width: `${scoreComercial}%`,
                  }}
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
              <p className="text-xs text-gray-400 uppercase">
                Crescimento
              </p>

              <p className="text-2xl font-bold text-emerald-400 mt-2">
                {implementadora.crescimento ?? 0}%
              </p>
            </div>

            <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
              <p className="text-xs text-gray-400 uppercase">
                Market Share
              </p>

              <p className="text-2xl font-bold text-cyan-400 mt-2">
                {implementadora.marketShare ?? 0}%
              </p>
            </div>

            <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
              <p className="text-xs text-gray-400 uppercase">
                Dominância
              </p>

              <p className="text-2xl font-bold text-yellow-400 mt-2">
                {implementadora.dominanciaRegional ??
                  "Moderada"}
              </p>
            </div>

            <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-4">
              <p className="text-xs text-gray-400 uppercase">
                Oportunidades
              </p>

              <p className="text-2xl font-bold text-cyan-400 mt-2">
                {oportunidades}
              </p>
            </div>
          </div>

          <div className="bg-[#091a33] border border-[#13203f] rounded-3xl p-6">
            <h3 className="text-2xl font-bold text-white mb-6">
              Inteligência Territorial
            </h3>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-400">
                  Região Estratégica
                </p>

                <p className="text-cyan-400 font-bold text-2xl mt-2">
                  {implementadora.regiao}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-400">
                  Potencial Comercial
                </p>

                <p className="text-emerald-400 font-bold text-2xl mt-2">
                  {implementadora.potencialMercado ??
                    implementadora.potencial}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-400 mb-3">
                  DDDs Dominantes
                </p>

                <div className="flex flex-wrap gap-2">
                  {implementadora.ddds?.map((ddd) => (
                    <span
                      key={ddd}
                      className="px-4 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm"
                    >
                      {ddd}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-400">
                  Oportunidades Ativas
                </p>

                <p className="text-cyan-400 font-bold text-4xl mt-2">
                  {oportunidades}
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-5">
            <div className="bg-gradient-to-br from-red-500/10 to-red-500/5 border border-red-500/20 rounded-3xl p-6">
              <p className="text-sm text-gray-400 uppercase tracking-wide">
                Risco Concorrencial
              </p>

              <h3 className="text-4xl font-bold text-red-400 mt-4">
                {riscoConcorrencial}
              </h3>

              <p className="text-gray-400 mt-4 leading-relaxed">
                Concorrência regional apresenta movimentação relevante
                nas operações monitoradas.
              </p>
            </div>

            <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-500/5 border border-yellow-500/20 rounded-3xl p-6">
              <p className="text-sm text-gray-400 uppercase tracking-wide">
                Prioridade Estratégica
              </p>

              <h3 className="text-4xl font-bold text-yellow-400 mt-4">
                {prioridadeEstrategica}
              </h3>

              <p className="text-gray-400 mt-4 leading-relaxed">
                Região monitorada pela IA operacional do CTI.
              </p>
            </div>
          </div>

          <div className="bg-[#091a33] border border-[#13203f] rounded-3xl p-6">
            <h3 className="text-2xl font-bold text-white mb-6">
              Equipamentos Estratégicos
            </h3>

            <div className="flex flex-wrap gap-3">
              {(
                implementadora.equipamentosRelacionados ??
                implementadora.equipamentos
              )?.map((equipamento) => (
                <span
                  key={equipamento}
                  className={`
                    px-4 py-3 rounded-2xl text-sm border

                    ${
                      equipamento === "CARRIER"
                        ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                        : "bg-[#11203a] border-[#1b315f] text-white"
                    }
                  `}
                >
                  {equipamento}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-cyan-500/10 to-blue-500/5 border border-cyan-500/20 rounded-3xl p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                <span className="text-cyan-400 text-2xl">
                  ✦
                </span>
              </div>

              <div>
                <h3 className="text-2xl font-bold text-white">
                  IA Operacional CTI
                </h3>

                <p className="text-gray-400">
                  Inteligência contextual automatizada
                </p>
              </div>
            </div>

            <div className="space-y-5">
              <div className="bg-[#071226]/60 border border-cyan-500/10 rounded-2xl p-5">
                <p className="text-cyan-400 font-semibold mb-3">
                  ALERTA ESTRATÉGICO
                </p>

                <p className="text-gray-300 leading-relaxed">
                  {alertaIA}
                </p>
              </div>

              <div className="bg-[#071226]/60 border border-emerald-500/10 rounded-2xl p-5">
                <p className="text-emerald-400 font-semibold mb-3">
                  RECOMENDAÇÕES DA IA
                </p>

                <ul className="space-y-2 text-gray-300">
                  {recomendacoesIA.map((item) => (
                    <li key={item}>
                      • {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-[#071226]/60 border border-yellow-500/10 rounded-2xl p-5">
                <p className="text-yellow-400 font-semibold mb-3">
                  OPORTUNIDADE IDENTIFICADA
                </p>

                <p className="text-gray-300 leading-relaxed">
                  {oportunidadeIA}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-[#091a33] border border-[#13203f] rounded-3xl p-6">
            <h3 className="text-2xl font-bold text-white mb-6">
              Montadoras Relacionadas
            </h3>

            <div className="flex flex-wrap gap-3">
              {implementadora.montadorasRelacionadas?.map(
                (montadora) => (
                  <span
                    key={montadora}
                    className="px-4 py-3 rounded-2xl bg-[#11203a] border border-[#1b315f] text-white"
                  >
                    {montadora}
                  </span>
                )
              )}
            </div>
          </div>

          <div className="bg-[#091a33] border border-[#13203f] rounded-3xl p-6">
            <h3 className="text-2xl font-bold text-white mb-6">
              Timeline Operacional
            </h3>

            <div className="space-y-5">
              {implementadora.eventos?.map(
                (evento, index) => {
                  const colorMap = {
                    positivo:
                      "bg-emerald-400",

                    alerta:
                      "bg-yellow-400",

                    negativo:
                      "bg-red-400",

                    estrategico:
                      "bg-cyan-400",
                  }

                  return (
                    <div
                      key={index}
                      className="
                        flex items-start gap-4
                        pb-5 border-b border-[#13203f]
                      "
                    >
                      <div
                        className={`
                          w-4 h-4 rounded-full mt-1
                          ${colorMap[evento.tipo]}
                        `}
                      />

                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-white font-semibold">
                            {evento.titulo}
                          </p>

                          <span className="text-xs text-gray-500">
                            {evento.data}
                          </span>
                        </div>

                        <p className="text-gray-400 mt-2 leading-relaxed">
                          {evento.descricao}
                        </p>
                      </div>
                    </div>
                  )
                }
              )}
            </div>
          </div>

          <div className="bg-[#091a33] border border-[#13203f] rounded-3xl p-6 mb-10">
            <h3 className="text-2xl font-bold text-white mb-6">
              Observações Estratégicas
            </h3>

            <p className="text-gray-300 leading-relaxed text-lg">
              {implementadora.observacoes}
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}