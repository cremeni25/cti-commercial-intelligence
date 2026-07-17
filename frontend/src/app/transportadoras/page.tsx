"use client"

import ModuloListaPage from "@/components/ModuloListaPage"
import { getTransportadoras } from "@/services/modulos-api"

export default function TransportadorasPage() {
  return (
    <ModuloListaPage
      titulo="Transportadoras"
      subtitulo="Carteira operacional derivada dos clientes presentes nos registros reais do CTI."
      carregar={getTransportadoras}
    />
  )
}
