import { redirect } from "next/navigation"

export default async function OportunidadeEncerradaDetalhe({params}:{params:Promise<{id:string}>}){
  const {id}=await params
  redirect(`/oportunidades/${encodeURIComponent(id)}`)
}
