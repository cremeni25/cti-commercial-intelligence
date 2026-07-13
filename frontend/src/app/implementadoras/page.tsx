"use client"

import { useEffect, useMemo, useState } from "react"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

import ImplementadorasTable from "@/modules/implementadoras/components/ImplementadorasTable"
import ImplementadorasDrawer from "@/modules/implementadoras/components/ImplementadoraDrawer"
import ImplementadorasFilters from "@/modules/implementadoras/components/ImplementadorasFilters"

import { Implementadora } from "@/modules/implementadoras"

import { apiGet } from "@/core/api"

export default function ImplementadorasPage() {
  const [implementadoras, setImplementadoras] = useState<Implementadora[]>([])
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("Todos")

  const [selected, setSelected] =
    useState<Implementadora | null>(null)

  const [drawerOpen, setDrawerOpen] =
    useState(false)

  useEffect(() => {
    carregarImplementadoras()
  }, [])

  async function carregarImplementadoras() {
    try {
      setLoading(true)

      const data =
        await apiGet("/implementadoras")

      setImplementadoras(data)
    } catch (e) {
      console.error(e)
      setImplementadoras([])
    } finally {
      setLoading(false)
    }
  }

  const lista = useMemo(() => {
    return implementadoras.filter((item) => {

      const okStatus =
        status === "Todos"
          ? true
          : item.status === status

      const okSearch =
        item.nome
          .toLowerCase()
          .includes(search.toLowerCase())

      return okStatus && okSearch
    })
  }, [implementadoras, search, status])

  function abrirDrawer(
    implementadora: Implementadora
  ) {
    setSelected(implementadora)
    setDrawerOpen(true)
  }

  return (
    <main className="flex min-h-screen bg-[#020817]">

      <Sidebar />

      <section className="flex-1">

        <Topbar />

        <div className="p-8 space-y-8">

          <ImplementadorasFilters
            search={search}
            setSearch={setSearch}
            status={status}
            setStatus={setStatus}
          />

          {loading ? (

            <div className="text-center text-cyan-400 py-20">
              Carregando Implementadoras...
            </div>

          ) : (

            <ImplementadorasTable
              implementadoras={lista}
              onSelectImplementadora={abrirDrawer}
            />

          )}

        </div>

      </section>

      <ImplementadorasDrawer
        implementadora={selected}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

    </main>
  )
}