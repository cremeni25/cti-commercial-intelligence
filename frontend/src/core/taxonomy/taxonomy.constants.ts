export const PRODUTOS_OFICIAIS = {
  TR: "Trailer",
  DT: "Diesel Truck",
  DD: "Direct Drive",
} as const

export const PRODUTOS_ALIAS = {
  TRAILER: "TR",
  TR: "TR",

  DIESELTRUCK: "DT",
  DIESEL_TRUCK: "DT",
  "DIESEL TRUCK": "DT",
  DT: "DT",

  DIRECTDRIVE: "DD",
  DIRECT_DRIVE: "DD",
  "DIRECT DRIVE": "DD",
  DD: "DD",
} as const

export const IMPLEMENTADORAS_OFICIAIS = {
  RANDON: "Randon",
  IBIPORA: "Ibiporã",
  SULBRASIL: "SulBrasil",
  MERCOSUL: "Mercosul",
  NIJU: "Niju",
  FACCHINI: "Facchini",
  FIBRASIL: "Fibrasil",
  LABONIA: "Labonia",
  HC: "HC",
  PAVAN: "Pavan",
} as const

export const IMPLEMENTADORAS_ALIAS = {
  RANDON: "RANDON",

  IBIPORA: "IBIPORA",
  IBIPORÃ: "IBIPORA",

  SULBRASIL: "SULBRASIL",
  "SUL BRASIL": "SULBRASIL",
  SUL_BRASIL: "SULBRASIL",

  MERCOSUL: "MERCOSUL",

  NIJU: "NIJU",

  FACCHINI: "FACCHINI",

  FIBRASIL: "FIBRASIL",

  LABONIA: "LABONIA",

  HC: "HC",

  PAVAN: "PAVAN",
} as const

export const CONCORRENTES_OFICIAIS = {
  THERMOKING: "Thermo King",
  FRIGOKING: "Frigoking",
  THERMOSTAR: "Thermostar",
  RODOFRIO: "Rodofrio",
  THERMOFLEX: "Thermoflex",
} as const

export const CONCORRENTES_ALIAS = {
  THERMOKING: "THERMOKING",
  "THERMO KING": "THERMOKING",

  FRIGOKING: "FRIGOKING",
  "FRIGO KING": "FRIGOKING",

  THERMOSTAR: "THERMOSTAR",

  RODOFRIO: "RODOFRIO",

  THERMOFLEX: "THERMOFLEX",
  "THERMO FLEX": "THERMOFLEX",
} as const

export const MONTADORAS_OFICIAIS = {
  VOLVO: "Volvo",
  SCANIA: "Scania",
  MERCEDES: "Mercedes",
  IVECO: "Iveco",
  VW: "Volkswagen",
  DAF: "DAF",
} as const

export const MONTADORAS_ALIAS = {
  VOLVO: "VOLVO",

  SCANIA: "SCANIA",

  MERCEDES: "MERCEDES",
  MERCEDESBENZ: "MERCEDES",
  "MERCEDES BENZ": "MERCEDES",

  IVECO: "IVECO",

  VW: "VW",
  VOLKSWAGEN: "VW",

  DAF: "DAF",
} as const

export const STATUS_OFICIAIS = [
  "ATIVO",
  "INATIVO",
  "PENDENTE",
  "PROCESSANDO",
] as const

export const PIPELINE_STATUS = [
  "UPLOAD",
  "NORMALIZADO",
  "VALIDADO",
  "CLASSIFICADO",
  "PROCESSADO",
] as const