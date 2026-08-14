# HIST-001 — Contrato de ingestão do histórico comercial 2023–2026

## Escopo
Parser read-only para `funil de vendas 2026.xlsx`. Não grava em Supabase e não integra staging bruto ao Pipeline, Forecast, Pedidos, Vendas, Clientes ou IA.

## Fonte e proveniência
- Abas obrigatórias: `BACKLOG`, `OPORTUNIDADE`, `INTERMEDIAÇÃO - OEM`.
- Cabeçalho real: linha 5.
- Dados comerciais: a partir da linha 6.
- Cada saída preserva `arquivo_origem`, SHA-256 do arquivo, `aba_origem`, `linha_origem`, fotografia `registro_original` e `registro_hash` determinístico.
- Intervalos auditados: BACKLOG A:O, OPORTUNIDADE A:N e INTERMEDIAÇÃO - OEM A:H.
- Colunas sem cabeçalho permanecem dentro de `registro_original`; não são promovidas a atributos comerciais por posição.

## Semântica
- `BACKLOG` não implica automaticamente ganho/faturamento.
- `OPORTUNIDADE` preserva probabilidade original; probabilidade zero é sinalizada como não confiável, não substituída por percentual inventado.
- `INTERMEDIAÇÃO - OEM` produz `canal_venda=INDIRETA_OEM`; cliente final permanece cliente do negócio e implementadora é relacionamento do canal.
- Nas linhas OEM em que F/G mudaram de semântica para preço unitário/total, o parser detecta evidência financeira por fórmula/conteúdo e não interpreta cegamente o cabeçalho.

## Continuidade territorial
- `representante_original` nunca é sobrescrito.
- Registros de CARLA são normalizados para `MÔNICA - VIENA SP`, refletindo a substituição territorial aprovada.
- A flag `REPRESENTANTE_SUBSTITUIDO_CARLA_POR_MONICA` mantém a explicabilidade da reconciliação.

## Taxonomia
- Clientes reutilizam a consolidação central existente.
- Implementadoras reutilizam `core.cti_taxonomy.normalizar_implementadora`.
- Grafias não reconhecidas continuam rastreáveis; não são descartadas.

## Barreira operacional
Este módulo não importa repositórios, clientes HTTP, Supabase ou serviços de mutação. HIST-001 termina em estruturas Python em memória e testes. DDL/staging pertence à HIST-002 e requer autorização própria.

## Direção analítica futura
ANFIR homologado, histórico comercial homologado e CRM atual permanecem fontes distintas por proveniência e podem convergir posteriormente em camada analítica reconciliada. O staging bruto não é fonte oficial da IA.
