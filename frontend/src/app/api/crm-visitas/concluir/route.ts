import { NextRequest, NextResponse } from "next/server"

const BACKEND_CTI = "https://cti-backend-5ugf.onrender.com"

type Payload = {
  visita_id: string
  cliente_id: string
  oportunidade_id?: string | null
  usuario_id: string
  descricao: string
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

export async function POST(request: NextRequest) {
  const dados = (await request.json().catch(() => null)) as Payload | null
  if (!dados?.visita_id || !dados.cliente_id || !dados.usuario_id || !dados.descricao) {
    return NextResponse.json({ detail: "Dados obrigatórios da visita não informados." }, { status: 422 })
  }

  const conclusao = await chamada(`/crm/atividades/${encodeURIComponent(dados.visita_id)}`, {
    method: "PUT",
    body: JSON.stringify({ status: "CONCLUIDA", descricao: dados.descricao }),
  })
  if (!conclusao.resposta.ok) {
    return NextResponse.json(
      { detail: conclusao.corpo?.detail || "Não foi possível concluir a visita." },
      { status: conclusao.resposta.status },
    )
  }

  let proximaAcao: unknown = null
  if (dados.proxima_acao?.trim() && dados.proxima_data) {
    const followup = await chamada("/crm/atividades", {
      method: "POST",
      body: JSON.stringify({
        cliente_id: dados.cliente_id,
        oportunidade_id: dados.oportunidade_id || null,
        usuario_id: dados.usuario_id,
        tipo: "FOLLOW_UP",
        titulo: dados.proxima_acao.trim(),
        descricao: "Próxima ação definida no encerramento de visita comercial.",
        data: dados.proxima_data,
        horario: null,
        status: "PENDENTE",
      }),
    })

    if (!followup.resposta.ok) {
      await chamada(`/crm/atividades/${encodeURIComponent(dados.visita_id)}`, {
        method: "PUT",
        body: JSON.stringify({ status: "EM_ANDAMENTO" }),
      }).catch(() => null)
      return NextResponse.json(
        { detail: followup.corpo?.detail || "A próxima ação falhou; a visita permaneceu em andamento." },
        { status: followup.resposta.status },
      )
    }
    proximaAcao = followup.corpo
  }

  return NextResponse.json({
    success: true,
    visita: conclusao.corpo,
    proxima_acao: proximaAcao,
    sincronizacao: "CRM_APP_SITE_CTI",
  })
}
