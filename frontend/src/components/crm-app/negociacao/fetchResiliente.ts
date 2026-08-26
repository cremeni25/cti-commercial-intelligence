export async function fetchLeituraResiliente(input: RequestInfo | URL, init: RequestInit = {}, tentativas = 3): Promise<Response> {
  let ultima: Response | null = null
  for (let tentativa = 0; tentativa < tentativas; tentativa += 1) {
    try {
      const resposta = await fetch(input, { ...init, cache: init.cache ?? "no-store" })
      ultima = resposta
      if (![500, 502, 503, 504].includes(resposta.status) || tentativa + 1 >= tentativas) return resposta
    } catch (erro) {
      if (tentativa + 1 >= tentativas) throw erro
    }
    await new Promise((resolve) => window.setTimeout(resolve, 160 * (tentativa + 1)))
  }
  if (ultima) return ultima
  throw new Error("Fonte de dados temporariamente indisponível.")
}
