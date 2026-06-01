import { supabase } from "../database/supabase"

export async function buscarDashboardExecutivo() {
  const { data, error } = await supabase
    .from("cti_dashboard_executivo")
    .select("*")
    .limit(1)
    .single()

  if (error) {
    console.error(
      "[CTI] erro dashboard executivo",
      error
    )

    return null
  }

  return data
}