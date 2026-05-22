interface KPICardProps {
  title: string
  value: string
  change: string
  positive?: boolean
}

export function KPICard({
  title,
  value,
  change,
  positive = true,
}: KPICardProps) {
  return (
    <div className="relative overflow-hidden bg-[#071226] border border-[#13203f] rounded-2xl p-5 transition-all hover:border-cyan-500/30 hover:shadow-[0_0_30px_rgba(6,182,212,0.08)]">
      <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-3xl" />

      <div className="relative z-10 flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
            {title}
          </p>

          <h3 className="text-4xl font-bold text-cyan-400 mt-3">
            {value}
          </h3>

          <div
            className={`
              inline-flex items-center gap-2 mt-4 px-3 py-1 rounded-full text-xs font-semibold border

              ${
                positive
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                  : "bg-red-500/10 border-red-500/20 text-red-400"
              }
            `}
          >
            <span>
              {positive ? "▲" : "▼"}
            </span>

            {change}
          </div>
        </div>

        <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
          <span className="text-2xl text-cyan-400">
            ◫
          </span>
        </div>
      </div>

      <div className="relative z-10 mt-4">
        <div className="w-full h-2 rounded-full bg-[#11203a] overflow-hidden">
          <div
            className={`
              h-2 rounded-full

              ${
                positive
                  ? "bg-gradient-to-r from-cyan-400 to-emerald-400"
                  : "bg-gradient-to-r from-red-400 to-orange-400"
              }
            `}
            style={{
              width: positive ? "78%" : "42%",
            }}
          />
        </div>
      </div>
    </div>
  )
}