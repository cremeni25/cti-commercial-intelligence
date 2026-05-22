"use client"

interface Props {
  search: string
  setSearch: (value: string) => void
  status: string
  setStatus: (value: string) => void
}

export default function ImplementadorasFilters({
  search,
  setSearch,
  status,
  setStatus,
}: Props) {
  return (
    <div className="flex items-center justify-between gap-4 mb-6">
      {/* SEARCH */}
      <input
        type="text"
        placeholder="Buscar implementadora..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-3 text-white outline-none w-full"
      />

      {/* FILTER */}
      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-3 text-white outline-none"
      >
        <option value="Todos">Todos</option>
        <option value="Ativo">Ativos</option>
        <option value="Inativo">Inativos</option>
      </select>
    </div>
  )
}