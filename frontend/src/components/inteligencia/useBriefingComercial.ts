"use client"

import { useCallback, useEffect, useState } from "react"
import { useAuth } from "@/core/auth/AuthContext"
import { buscarBriefingComercial, type BriefingComercial } from "@/services/inteligencia-comercial"

type Estado = { chave: string; versao: number; briefing: BriefingComercial | null; erro: string }

/**
 * Carrega o briefing do agente para o usuário autenticado.
 * Cada resultado é marcado com a chave (usuário + responsável + limite) e a versão
 * da leitura: respostas antigas são descartadas e a troca de responsável nunca
 * exibe a carteira anterior.
 */
export function useBriefingComercial(opcoes: { responsavelId?: string; limite?: number } = {}) {
  const { usuario } = useAuth()
  const { responsavelId, limite } = opcoes
  const usuarioId = usuario?.id || ""
  const chave = `${usuarioId}|${responsavelId || ""}|${limite || ""}`
  const [versao, setVersao] = useState(0)
  const [estado, setEstado] = useState<Estado>({ chave: "", versao: -1, briefing: null, erro: "" })

  useEffect(() => {
    if (!usuarioId) return
    let ativo = true
    buscarBriefingComercial({ responsavelId, limite })
      .then((briefing) => { if (ativo) setEstado({ chave, versao, briefing, erro: "" }) })
      .catch((falha: unknown) => {
        if (!ativo) return
        const erro = falha instanceof Error ? falha.message : "Não foi possível carregar a leitura do agente."
        setEstado((anterior) => ({ chave, versao, briefing: anterior.chave === chave ? anterior.briefing : null, erro }))
      })
    return () => { ativo = false }
  }, [chave, versao, usuarioId, responsavelId, limite])

  const atualizar = useCallback(() => setVersao((atual) => atual + 1), [])
  const mesmaChave = estado.chave === chave

  return {
    briefing: mesmaChave ? estado.briefing : null,
    erro: mesmaChave ? estado.erro : "",
    carregando: !mesmaChave || estado.versao !== versao,
    atualizar,
  }
}
