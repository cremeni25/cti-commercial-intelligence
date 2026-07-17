"use client"

import ModuloListaPage from "@/components/ModuloListaPage"
import { getEmpresas } from "@/services/modulos-api"

export default function EmpresasPage() {
  return (
    <ModuloListaPage
      titulo="Empresas"
      subtitulo="Carteira operacional derivada das razões sociais presentes nos registros reais do CTI."
      carregar={getEmpresas}
    />
  )
}
