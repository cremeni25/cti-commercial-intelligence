type Registro = Record<string, unknown>
export type ClienteCarteira = {
  id: string; chave: string; nome: string; razaoSocial: string; nomeFantasia: string
  cnpj: string; cidade: string; estado: string; negocios: number; responsavel: string
}
const texto = (valor: unknown) => String(valor ?? "").trim()
const nomeNormalizado = (valor: unknown) => texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR")

export function montarCarteiraClientes(cadastro: Registro[], negocios: Registro[]): ClienteCarteira[] {
  const porChave = new Map<string, ClienteCarteira>()
  for (const item of cadastro) {
    const razaoSocial = texto(item.razao_social), nomeFantasia = texto(item.nome_fantasia)
    const nome = texto(item.nome || razaoSocial || nomeFantasia)
    if (!nome) continue
    const id = texto(item.id), cnpj = texto(item.cnpj || item.cnpj_cpf || item.documento)
    const documento = cnpj.replace(/\D/g, "")
    const chave = id ? `id:${id}` : documento ? `cnpj:${documento}` : `nome:${nomeNormalizado(nome)}`
    porChave.set(chave, { id: id || nome, chave, nome, razaoSocial, nomeFantasia, cnpj,
      cidade: texto(item.cidade || item.municipio), estado: texto(item.estado || item.uf).toUpperCase(),
      negocios: 0, responsavel: texto(item.responsavel_comercial_nome) })
  }
  const porNome = new Map<string, ClienteCarteira[]>()
  for (const cliente of porChave.values()) {
    const chave = nomeNormalizado(cliente.nome)
    porNome.set(chave, [...(porNome.get(chave) || []), cliente])
  }
  for (const item of negocios) {
    const clienteId = texto(item.cliente_id)
    const candidatos = porNome.get(nomeNormalizado(item.cliente_nome)) || []
    // Um ID explícito nunca pode cair no cadastro de outro cliente homônimo.
    const cliente = clienteId ? porChave.get(`id:${clienteId}`) : candidatos.length === 1 ? candidatos[0] : undefined
    if (cliente) cliente.negocios += 1
  }
  return [...porChave.values()]
}
