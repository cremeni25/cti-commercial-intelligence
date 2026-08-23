export type NegocioInstitucional = {
  slug: string
  nome: string
  parceiro: string
  status: string
  resumo: string
  descricao: string
  eixos: string[]
  temas: string[]
}

export type RadarItem = {
  slug: string
  categoria: string
  titulo: string
  resumo: string
  negocio: string
  status: string
}

export const negocios: NegocioInstitucional[] = [
  {
    slug: "viena-sao-paulo-carrier",
    nome: "Viena São Paulo",
    parceiro: "Carrier Transicold",
    status: "Vertical ativa",
    resumo:
      "Inteligência comercial aplicada à operação de refrigeração para transporte, conectando mercado, território, histórico e execução comercial.",
    descricao:
      "A operação Viena São Paulo | Carrier Transicold é a primeira vertical real acompanhada pelo CTI. A plataforma organiza sinais comerciais e de mercado para transformar informação dispersa em contexto, prioridade, acompanhamento e decisão, preservando em ambiente restrito todos os dados estratégicos da operação.",
    eixos: [
      "Performance comercial e evolução histórica",
      "Território, carteira e cobertura de mercado",
      "Equipamentos e linhas de refrigeração para transporte",
      "Pipeline, oportunidades e acompanhamento comercial",
      "Sinais de mercado e inteligência setorial",
      "Previsão, recomendação e apoio à decisão",
    ],
    temas: [
      "Cadeia do frio",
      "Transporte refrigerado",
      "Implementos rodoviários",
      "Eletrificação",
      "Logística",
      "Regulação e eventos do setor",
    ],
  },
]

export const radarItems: RadarItem[] = [
  {
    slug: "treinamento-comercial-viena",
    categoria: "Operação",
    titulo: "Treinamento comercial na Viena São Paulo",
    resumo:
      "Movimentos de capacitação da equipe passam a compor a leitura institucional do negócio e o contexto de evolução da operação comercial.",
    negocio: "Viena São Paulo | Carrier Transicold",
    status: "Contexto da operação",
  },
  {
    slug: "eletrificacao-refrigeracao-transporte",
    categoria: "Tecnologia",
    titulo: "Eletrificação entra no radar da refrigeração para transporte",
    resumo:
      "Novas soluções elétricas ampliam os temas acompanhados pelo CTI em tecnologia, eficiência, aplicação e transformação do mercado.",
    negocio: "Viena São Paulo | Carrier Transicold",
    status: "Tema em acompanhamento",
  },
  {
    slug: "agenda-setorial-fenatran-2026",
    categoria: "Agenda",
    titulo: "Fenatran 2026 integra a agenda setorial do Radar CTI",
    resumo:
      "Feiras, lançamentos e encontros do transporte passam a ser organizados como sinais de contexto para as verticais acompanhadas pela plataforma.",
    negocio: "Viena São Paulo | Carrier Transicold",
    status: "Agenda setorial",
  },
]

export const temasRadar = [
  "Cadeia do frio",
  "ANVISA e transporte de medicamentos",
  "Transporte e logística",
  "Refrigeração para transporte",
  "Eletrificação e novas tecnologias",
  "Feiras, treinamentos e lançamentos",
  "Indicadores econômicos relacionados aos negócios",
]
