import { NextRequest, NextResponse } from "next/server"

const BACKEND_CTI = "https://cti-backend-5ugf.onrender.com"

type Payload = {
  atividade_id: string
  cliente_id?: string
  oportunidade_id?: string | null
  usuario_id: string
  status_anterior?: string
  descricao_original?: string
  resultado: string
  desfecho: string
  proxima_acao?: string
  proxima_data?: string
}

async function chamada(caminho: string, init: RequestInit) {
  const resposta = await fetch(`${BACKEND_CTI}${caminho}`, {
    ...init,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
  })
  const corpo = await resposta.json().catch(() => ({}))
  return { resposta, corpo }
}

function historico(dados: Payload) {
  const original = dados.descricao_original?.trim() || "Não informado"
  const blocos = [
    `[PLANEJAMENTO ORIGINAL]\n${original}`,
    `[RESULTADO]\n${dados.resultado.trim()}`,
    `[DESFECHO]\n${dados.desfecho.trim()}`,
  ]
  if (dados.proxima_acao?.trim()) blocos.push(`[PRÓXIMA AÇÃO]\n${dados.proxima_acao.trim()}${dados.proxima_data ? `\nData: ${dados.proxima_data}` : ""}`)
  return blocos.join("\n\n")
}

export async function POST(request: NextRequest) {
  const dados = (await request.json().catch(() => null)) as Payload | null
  if (!dados?.atividade_id || !dados.usuario_id || !dados.resultado?.trim() || !dados.desfecho?.trim()) {
    return NextResponse.json({ detail: "Informe atividade, responsável, resultado e desfecho." }, { status: 422 })
  }
  if ((dados.proxima_acao?.trim() && !dados.proxima_data) || (!dados.proxima_acao?.trim() && dados.proxima_data)) {
    return NextResponse.json({ detail: "Próxima ação e data devem ser informadas em conjunto." }, { status: 422 })
  }

  const descricaoFinal = historico(dados)
  const conclusao = await chamada(`/crm/atividades/${encodeURIComponent(dados.atividade_id)}`, {
    method: "PUT",
    body: JSON.stringify({ status: "CONCLUIDA", descricao: descricaoFinal }),
  })
  if (!conclusao.resposta.ok) {
    return NextResponse.json({ detail: conclusao.corpo?.detail || "Não foi possível concluir a atividade." }, { status: conclusao.resposta.status })
  }

  let proximaAcao: unknown = null
  if (dados.proxima_acao?.trim() && dados.proxima_data) {
    const followup = await chamada("/crm/atividades", {
      method: "POST",
      body: JSON.stringify({
        cliente_id: dados.cliente_id || null,
        oportunidade_id: dados.oportunidade_id || null,
        usuario_id: dados.usuario_id,
        tipo: "FOLLOW_UP",
        titulo: dados.proxima_acao.trim(),
        descricao: `Próxima ação originada do encerramento da atividade ${dados.atividade_id}.`,
        data: dados.proxima_data,
        horario: null,
        status: "PENDENTE",
      }),
    })

    if (!followup.resposta.ok) {
      await chamada(`/crm/atividades/${encodeURIComponent(dados.atividade_id)}`, {
        method: "PUT",
        body: JSON.stringify({
          status: dados.status_anterior || "PENDENTE",
          descricao: dados.descricao_original || "",
        }),
      }).catch(() => null)
      return NextResponse.json({ detail: followup.corpo?.detail || "A próxima ação falhou; a atividade não foi encerrada." }, { status: followup.resposta.status })
    }
    proximaAcao = followup.corpo
  }

  return NextResponse.json({
    success: true,
    atividade: conclusao.corpo,
    proxima_acao: proximaAcao,
    descricao_historica: descricaoFinal,
  })
}
