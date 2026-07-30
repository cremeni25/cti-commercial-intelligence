import { redirect } from "next/navigation"

export default function NovaVisitaRedirect() {
  redirect("/crm-app/atividades/nova?tipo=VISITA")
}
