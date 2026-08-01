"use client"

import type { ReactNode } from "react"

type Registro = Record<string, unknown>

type Props = {
  proposta: Registro
  item: Registro | null
  oportunidade: Registro | null
  cliente: Registro | null
}

function texto(valor: unknown, padrao = "________________") {
  const resultado = String(valor ?? "").trim()
  return resultado || padrao
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function campo(objeto: Registro | null | undefined, ...chaves: string[]) {
  for (const chave of chaves) {
    const valor = objeto?.[chave]
    if (valor !== undefined && valor !== null && String(valor).trim()) return valor
  }
  return null
}

function Pagina({ children, numero }: { children: ReactNode; numero: number }) {
  return <section className="carrier-page relative mx-auto min-h-[1122px] w-full max-w-[794px] bg-white px-16 py-12 text-[13px] leading-[1.35] text-black shadow-xl print:min-h-[1122px] print:max-w-none print:shadow-none">
    <header className="mb-8 flex items-start justify-between">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Proposta comercial Carrier Transicold</div>
      <div className="text-right"><div className="text-2xl font-bold italic text-[#17468f]">Carrier</div><div className="text-[11px] font-bold tracking-[0.28em] text-[#17468f]">TRANSICOLD</div></div>
    </header>
    {children}
    <footer className="absolute bottom-0 left-0 right-0 h-14 overflow-hidden"><div className="absolute bottom-[-28px] left-[-40px] h-16 w-[115%] -rotate-2 bg-[#164697]"/><div className="absolute bottom-[6px] left-[-40px] h-4 w-[115%] -rotate-2 bg-white"/><span className="absolute bottom-2 right-6 text-[10px] text-white">Página {numero}</span></footer>
  </section>
}

export default function CarrierProposalDocument({ proposta, item, oportunidade, cliente }: Props) {
  const snapshot = (proposta.snapshot_dados || {}) as Registro
  const snapshotItem = (snapshot.item || {}) as Registro
  const snapshotOportunidade = (snapshot.oportunidade || {}) as Registro
  const equipamento = texto(campo(item, "equipamento") || campo(snapshotItem, "equipamento"), "SUPRA 750")
  const quantidade = texto(campo(item, "quantidade") || campo(snapshotItem, "quantidade"), "1")
  const valorUnitario = moeda(campo(item, "preco_unitario") || campo(snapshotItem, "preco_unitario") || proposta.valor)
  const valorTotal = moeda(proposta.valor)
  const nomeCliente = texto(campo(cliente, "razao_social", "nome_fantasia", "nome") || campo(oportunidade, "cliente_nome") || campo(snapshotOportunidade, "cliente_nome", "empresa_nome"))
  const validade = texto(campo(item, "validade_condicao") || snapshot.validade || proposta.validade, "Válido até o último dia do presente mês de envio")
  const condicao = texto(campo(item, "condicao_pagamento") || snapshot.condicoes_adicionais)
  const frete = texto(campo(item, "frete"))
  const entrega = texto(campo(item, "local_entrega"))
  const opcionais = Array.isArray(item?.opcionais) ? (item?.opcionais as unknown[]).join(", ") : texto(campo(item, "opcionais"), "Nenhum")
  const data = proposta.emitida_em || proposta.created_at || new Date().toISOString()
  const dataFormatada = new Date(String(data)).toLocaleDateString("pt-BR")

  return <div className="space-y-8 print:space-y-0">
    <Pagina numero={1}>
      <p className="font-bold">Data: {dataFormatada}</p>
      <div className="mt-6 font-bold"><p>Empresa para faturamento (OBRIGATÓRIO):</p><p>Carrier Refrigeração Brasil Ltda</p><p>( ) RS: 03.646.086/0001-12</p><p>( ) GO: 03.646.086/0008-99</p></div>
      <table className="mt-6 w-full border-collapse text-[12px]"><tbody>
        <CampoTabela titulo="Nome do cliente" valor={nomeCliente}/><CampoTabela titulo="CPF/CNPJ" valor={texto(campo(cliente, "cnpj", "cpf_cnpj"))}/><CampoTabela titulo="INSC" valor={texto(campo(cliente, "inscricao_estadual"))}/><CampoTabela titulo="Endereço Completo" valor={texto(campo(cliente, "endereco", "endereco_completo"))}/><CampoTabela titulo="Telefones de contato" valor={texto(campo(cliente, "telefone", "celular"))}/><CampoTabela titulo="E-mail" valor={texto(campo(cliente, "email"))}/>
      </tbody></table>
      <div className="mt-6"><p className="font-bold">Ref.: Unidades p/ Refrigeração</p><p>Segue para apreciação nossa proposta venda de {quantidade} equipamento(s) de refrigeração conforme dados abaixo:</p></div>
      <div className="mt-4 grid grid-cols-[180px_1fr] gap-x-4"><p className="font-bold italic">Modelo do Equipamento:</p><p className="font-bold">{equipamento}</p><p className="font-bold italic">Especificações técnicas:</p><div className="italic"><p>20.500 Btu/h a 2°C</p><p>7.500 Btu/h a -29°C</p><p>Vazão de ar em alta/baixa velocidade: 2.400 m³/h</p><p>Gás Refrigerante R 404 A</p><p>Compressor Carrier / Modelo 05K de 2cc</p><p>Controle microprocessado com códigos de falha e módulo remoto na cabine</p><p>Motor Diesel Kubota</p><p>Motor elétrico Stand by 220V/380V automático</p><p>Kit instalação</p></div></div>
      <p className="mt-4"><strong>Instalação:</strong> Deverá ser instalado na rede Carrier.</p>
      <table className="mt-5 w-full border-collapse text-[12px]"><tbody><CampoTabela titulo="Quantidade" valor={quantidade}/><CampoTabela titulo="Valor unitário desta proposta" valor={valorUnitario}/><CampoTabela titulo="Valor Total desta proposta" valor={valorTotal}/><CampoTabela titulo="Impostos inclusos" valor="04% ICMS/PIS/COFINS"/><CampoTabela titulo="Acessórios / Itens Complementares" valor={opcionais}/><CampoTabela titulo="Condições de pagamentos" valor={condicao}/><CampoTabela titulo="Possui Entrada?" valor="( ) SIM   ( ) NÃO"/><CampoTabela titulo="Valor" valor="________________"/><CampoTabela titulo="Entrega" valor={`Autorizada Carrier ( )  Endereço cliente ( )  ${entrega}`}/><CampoTabela titulo="Frete" valor={`( ) CIF  ( ) FOB  ${frete}`}/></tbody></table>
      <p className="mt-2 font-bold">Validade da proposta: {validade}</p>
    </Pagina>

    <Pagina numero={2}>
      <p>Obs.: No dia da emissão da nota fiscal de faturamento será observada a cotação do dólar americano informada pelo Banco Central no fechamento do dia útil anterior ao faturamento e, caso a cotação frente ao Real tenha sofrido variação superior ao limite definido pela Carrier, os preços poderão ser alterados proporcionalmente.</p>
      <p className="mt-5">OBS: A tributação de ICMS de 04% será atribuída somente para casos em que o cliente possua Inscrição Estadual ativa.</p>
      <div className="mt-10 text-center"><div className="mx-auto w-64 border-t border-black pt-2">Assinatura e carimbo</div></div>
      <h2 className="mt-10 text-center font-bold underline">Dados de Aplicação</h2>
      <div className="mt-4 grid grid-cols-3 border border-black"><Quadro titulo="Dados do Baú" linhas={["Largura (m)","Comprimento (m)","Altura (m)","Divisória (m)","Portas (qtd)"]}/><Quadro titulo="Isolamento" linhas={["Tipo","Frente (cm)","Teto (cm)","Lateral (cm)","Piso (cm)","Porta (cm)"]}/><Quadro titulo="Aplicabilidade" linhas={["Temp. de Transporte (°C)","Nº de Abertura de Porta","Duração Abertura (min)","Período de Entrega (hs)"]}/></div>
      <h2 className="mt-7 text-lg font-bold">Condições de venda e fornecimento Carrier Refrigeração Brasil Ltda.</h2><h3 className="mt-4 font-bold">1. Limitação de responsabilidades:</h3><p className="mt-2 text-justify">Ficando comprovado que a CARRIER REFRIGERAÇÃO BRASIL LTDA. incorreu em erros, perdas ou danos por sua ação ou omissão voluntária, negligência ou imprudência, obriga-se a ressarcir a CLIENTE ou terceiros pelos prejuízos acarretados, limitado o valor máximo de indenização ao valor deste contrato, ressalvadas as hipóteses legais aplicáveis.</p><h3 className="mt-4 font-bold">2. Danos indiretos e lucros cessantes:</h3><p className="mt-2 text-justify">Nenhuma das partes responderá por lucros cessantes e danos indiretos decorrentes deste contrato.</p>
    </Pagina>

    <Pagina numero={3}>
      <h3 className="font-bold">3. Garantia:</h3><p className="mt-2 text-justify">Os equipamentos, desde que utilizados para os fins a que se destinam e submetidos à manutenção periódica na rede credenciada Carrier, possuem garantia de 24 meses para Motor Diesel e Compressor e 12 meses para os demais componentes, contados da instalação e expedição do certificado de garantia.</p><p className="mt-3 text-justify">A inobservância das orientações, recomendações e instruções fornecidas pela Carrier, especialmente as constantes do certificado de garantia, acarretará a perda da garantia.</p><table className="mx-auto mt-5 border-collapse"><tbody><tr><th className="border border-black px-5 py-1">Revisão</th><th className="border border-black px-5 py-1">Horas de utilização</th></tr>{[1000,2000,3000,4000].map((hora, i)=><tr key={hora}><td className="border border-black px-5 py-1">{i+1}ª Revisão</td><td className="border border-black px-5 py-1">{hora}h</td></tr>)}</tbody></table><h3 className="mt-6 font-bold">4. Força maior:</h3><p className="mt-2 text-justify">Nenhuma das partes será considerada em mora ou inadimplente se o atraso ou descumprimento decorrer de caso fortuito ou força maior, nos termos do Código Civil Brasileiro.</p><h3 className="mt-6 font-bold">5. Responsabilidade social e ambiental:</h3><p className="mt-2 text-justify">As partes declaram adotar condutas política, social e ambientalmente responsáveis, comprometendo-se a não utilizar trabalho ilegal, escravo ou infantil, a não praticar discriminação e a preservar o meio ambiente em observância à legislação aplicável.</p>
    </Pagina>

    <Pagina numero={4}>
      <h3 className="font-bold">6. Declaração de adequação de dimensionamento do equipamento:</h3><p className="mt-2 text-justify">O CLIENTE declara que as informações de capacidade e aplicação refletem fielmente as características do baú frigorífico e a temperatura necessária para o transporte, responsabilizando-se por prejuízos decorrentes de utilização em desacordo com as informações fornecidas.</p><h3 className="mt-6 font-bold">7. Condições em caso de parcelamento:</h3><p className="mt-2 text-justify">A CARRIER REFRIGERAÇÃO poderá ceder ou transferir os direitos e garantias decorrentes deste contrato. Informações de crédito poderão ser registradas no SCR do Banco Central conforme autorização e legislação aplicável.</p><p className="mt-4 font-bold">Em caso de inadimplência, incidirão multa de 2% e juros moratórios de 1% ao mês sobre a obrigação vencida e não paga.</p><h3 className="mt-7 font-bold">8. Confirmação de encomenda:</h3><p className="mt-2 text-justify font-bold">Para reconhecimento do fornecimento e confirmação da venda pela CARRIER REFRIGERAÇÃO, será necessário o reconhecimento formal de aceitação do conteúdo deste documento, mencionando o número da proposta e sua respectiva revisão.</p><p className="mt-3 text-justify">A aceitação desta proposta implica concordância expressa com suas condições de venda e fornecimento.</p>
    </Pagina>

    <Pagina numero={5}>
      <p className="text-justify">Na hipótese de condições especiais, estas deverão constar expressamente nos Pedidos ou Contratos.</p><p className="mt-5 font-bold">A titularidade dos equipamentos fornecidos pela CARRIER REFRIGERAÇÃO BRASIL LTDA. será transmitida ao comprador quando da entrega ao transportador.</p><h3 className="mt-8 font-bold">9. Pagamentos através de Boleto Bancário</h3><p className="mt-2 text-justify">Os boletos de cobrança em favor da Carrier Transicold são emitidos exclusivamente por instituição autorizada e terão como beneficiário final Carrier Refrigeração Brasil Ltda., CNPJ 03.646.086/0001-12 ou 03.646.086/0008-99.</p><h3 className="mt-8 font-bold">10. Da Proteção de Dados Pessoais</h3><p className="mt-2 text-justify">A Carrier Transicold declara observar a Lei nº 13.709/2018 e exige de seus clientes o mesmo cumprimento, tratando dados pessoais exclusivamente para as finalidades estabelecidas nesta proposta.</p><p className="mt-10">Cachoeirinha, ____ de __________ de 20____</p><p className="mt-8 font-bold">Atenciosamente.</p><div className="mt-16 grid grid-cols-2 gap-x-20 gap-y-14"><Assinatura titulo="CARRIER REFRIGERAÇÃO"/><Assinatura titulo="CLIENTE"/><Assinatura titulo="AVALISTA"/><Assinatura titulo="TESTEMUNHA 1"/><Assinatura titulo="TESTEMUNHA 2"/></div>
      <div className="mt-12 border-t border-dashed border-slate-400 pt-4 text-[10px] text-slate-600"><p>Proposta: {texto(proposta.numero)} • Revisão: {texto(proposta.versao, "1")}</p><p>Hash documental: {texto(proposta.hash_documento)}</p></div>
    </Pagina>
  </div>
}

function CampoTabela({ titulo, valor }: { titulo: string; valor: string }) { return <tr><th className="w-[38%] border border-black px-2 py-1 text-left">{titulo}:</th><td className="border border-black px-2 py-1">{valor}</td></tr> }
function Quadro({ titulo, linhas }: { titulo: string; linhas: string[] }) { return <div className="min-h-40 border-r border-black p-3 last:border-r-0"><p className="font-bold">{titulo}</p>{linhas.map((linha)=><p key={linha} className="mt-2">{linha}: __________</p>)}</div> }
function Assinatura({ titulo }: { titulo: string }) { return <div><div className="border-t border-black pt-2 font-bold">{titulo}</div></div> }
