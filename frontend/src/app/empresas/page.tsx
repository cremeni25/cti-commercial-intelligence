"use client"

import ModuloListaPage from "@/components/ModuloListaPage"
import { getClientes } from "@/services/modulos-api"

export default function EmpresasPage() {
  return (
    <ModuloListaPage
      titulo="Cadastro Mestre de Clientes"
      subtitulo="Visão consolidada dos clientes, ativos identificados e informações comerciais presentes nos registros do CTI."
      carregar={getClientes}
      cadastroMestre
    />
  )
}
