# HIST-007 — Proposta formal de promoção do histórico comercial

Status: **PROPOSTA FORMAL CONCLUÍDA — PROMOÇÃO NÃO AUTORIZADA NESTA EXECUÇÃO**

Data de referência: 2026-08-14

## 1. Objetivo

Formalizar como o histórico comercial 2023–2026 poderá sair do ambiente de homologação e ingressar em uma camada histórica/analítica oficial do CTI, sem contaminar o CRM operacional.

Esta execução **não promove registros**, não cria oportunidades ativas, não altera Pipeline, Forecast, Pedidos, Vendas, Clientes nem libera o histórico para a IA oficial.

## 2. Fonte homologada

Arquivo imutável: `funil de vendas 2026(20260814-104652).xlsx`

SHA-256: `54bb20087d96013e5a814a1d378f37315987c56b4a617631bd9603725ebb4583`

Volume homologado visualmente:

- BACKLOG: 277 registros
- OPORTUNIDADE: 518 registros
- INTERMEDIAÇÃO - OEM: 111 registros
- Total: 906 registros
- Canal DIRETA: 795
- Canal INDIRETA_OEM: 111
- 2023: 33
- 2024: 381
- 2025: 307
- 2026: 185
- Unidades nominais: 3.116
- Valor nominal de auditoria: R$ 193.255.897,40
- Divergências aritméticas identificadas: 0

O valor nominal acima é medida de auditoria e **não deve ser classificado automaticamente como receita, faturamento ou venda realizada**.

## 3. Estado técnico antes de qualquer promoção

As execuções HIST-001 a HIST-006 foram concluídas e homologadas.

O schema privado `historico_staging` existe e permanece isolado. No encerramento da HIST-006 ele continuava sem carga física dos 906 registros.

Consequência: ainda não existe manifesto persistido com a classificação final, registro a registro, de:

- cliente reconciliado / ambíguo / não encontrado;
- equipamento reconciliado / não encontrado;
- implementadora reconciliada / ambígua / não encontrada;
- representante reconciliado / não individualizado;
- erro, aviso, bloqueio e rejeição por registro.

Sem esses quantitativos finais, **nenhuma promoção deve ser executada**.

## 4. Decisão de arquitetura

O histórico homologado não deve ser promovido para tabelas operacionais existentes.

É proibida a promoção direta para, entre outras:

- `cti_oportunidades_registros`;
- `cti_pipeline` ou `pipeline`;
- `cti_pedidos`;
- `vendas` / `vendas_realizadas`;
- `clientes` como mecanismo de sobrescrita;
- qualquer fonte oficial consumida pela IA Comercial.

O destino futuro recomendado é uma camada histórica/analítica dedicada, por exemplo `analytics_comercial`, alimentada somente por dados homologados e com proveniência preservada.

Fluxo obrigatório:

`arquivo original imutável -> historico_staging -> normalização -> reconciliação -> auditoria -> manifesto de promoção -> homologação humana -> camada histórica/analítica oficial`

Nunca:

`planilha -> Pipeline/CRM ativo`

## 5. Unidade de promoção

A unidade promovível é o **registro histórico individual rastreável**.

Cada registro deverá manter permanentemente:

- arquivo de origem;
- SHA-256 da fonte;
- aba de origem;
- linha original;
- payload original;
- hash determinístico do registro;
- valores originais e normalizados;
- decisões de reconciliação;
- confiança de normalização/reconciliação;
- flags de qualidade;
- data e responsável pela homologação;
- versão do contrato/parser/normalizador/reconciliador.

## 6. Regra de elegibilidade para promoção

Um registro somente poderá entrar na camada histórica/analítica oficial quando:

1. pertencer à fonte de SHA-256 homologado;
2. possuir proveniência completa arquivo -> aba -> linha;
3. não apresentar erro ou bloqueio estrutural;
4. possuir quantidade/valor preservados sem correção silenciosa;
5. possuir canal classificado como `DIRETA` ou `INDIRETA_OEM`;
6. preservar cliente original mesmo quando não reconciliado;
7. preservar equipamento original quando modelo histórico não existir no catálogo atual;
8. preservar implementadora original e ambiguidade quando aplicável;
9. preservar representante histórico e responsabilidade territorial atual sem apagar autoria;
10. possuir decisão explícita de promoção no manifesto final.

## 7. Tratamento das reconciliações

### 7.1 Clientes

Hierarquia aprovada:

1. CNPJ válido e exato;
2. nome canônico normalizado exato;
3. similaridade de alta confiança com evidência;
4. ambíguo — revisão humana;
5. não encontrado — preservar como cliente histórico não reconciliado.

Ausência de CNPJ **não invalida** o registro histórico.

Não é permitido criar ou sobrescrever cliente operacional automaticamente durante a promoção histórica.

### 7.2 Representantes

A autoria histórica deve ser preservada.

Regra obrigatória CARLA -> MÔNICA:

- `representante_original = CARLA - VIENA SP` permanece consultável;
- responsabilidade territorial atual = `MÔNICA - VIENA SP`;
- flag explícita de substituição;
- nenhum dado histórico é reescrito como se Mônica tivesse realizado originalmente a ação.

`VIENA SP` sem pessoa identificada permanece não individualizado; não pode ser atribuído arbitrariamente a Anderson ou a outro vendedor.

### 7.3 Equipamentos

Match automático somente quando a identidade do modelo for segura.

Modelos históricos fora do catálogo atual permanecem válidos como histórico e devem ficar `NAO_ENCONTRADO`, sem descarte e sem associação aproximada indevida.

### 7.4 Implementadoras / OEM

O canal OEM é uma relação da negociação com o cliente final.

Não criar segunda oportunidade para a implementadora.

Estrutura:

`cliente final -> negócio histórico -> equipamento -> INDIRETA_OEM -> implementadora`

Relações compostas ou ambíguas devem permanecer explícitas para revisão humana.

## 8. Status e probabilidade

BACKLOG, OPORTUNIDADE e OEM não definem sozinhos o status comercial.

O status deve continuar reconstruído por evidência, preservando o texto original.

Probabilidades históricas preenchidas com zero na aba OPORTUNIDADE não devem ganhar valores artificiais. O zero original permanece preservado e a confiança pode ser classificada como não confiável.

## 9. Política para registros ambíguos

Ambiguidade não implica exclusão do histórico.

A camada histórica/analítica poderá armazenar o fato histórico com entidades não reconciliadas, desde que:

- o original esteja preservado;
- o status de reconciliação esteja explícito;
- nenhuma chave operacional incorreta seja atribuída;
- o registro não seja usado como verdade operacional de cliente/equipamento/implementadora.

## 10. Manifesto obrigatório antes da promoção

Antes de qualquer escrita na camada histórica/analítica oficial deverá ser gerado e homologado um manifesto contendo, no mínimo:

- total lido por aba;
- total válido / inválido;
- total rejeitado;
- duplicidades candidatas;
- clientes reconciliados;
- clientes ambíguos;
- clientes não encontrados;
- equipamentos reconciliados;
- equipamentos não encontrados;
- implementadoras reconciliadas;
- implementadoras ambíguas;
- implementadoras não encontradas;
- representantes reconciliados / não individualizados;
- distribuição por ano;
- distribuição por status;
- motivos de perda;
- DIRETA x INDIRETA_OEM;
- unidades;
- valores nominais;
- divergências aritméticas;
- flags de erro/aviso/bloqueio;
- quantidade efetivamente elegível para promoção;
- quantidade bloqueada;
- impacto esperado nos dashboards analíticos.

Esse manifesto deve ser reproduzível a partir do SHA-256 da fonte.

## 11. Impacto analítico esperado após futura promoção

A camada histórica/analítica oficial poderá habilitar leitura cruzada, sem alterar o CRM ativo, de:

- mercado observado ANFIR;
- histórico comercial Viena;
- CRM atual.

Filtros previstos:

- período;
- cliente;
- representante histórico;
- responsável territorial atual;
- região / DDD;
- equipamento;
- linha de produto;
- canal;
- implementadora;
- status;
- motivo de perda.

Indicadores futuros possíveis:

- conversão histórica;
- ciclo comercial;
- perda por preço/concorrência/sem retorno;
- mix de produto;
- recorrência por cliente;
- participação de implementadoras no canal indireto;
- memória comercial territorial;
- comparação histórico comercial x mercado ANFIR x execução atual.

A IA Comercial somente poderá consumir essa camada depois de homologação específica de fonte e governança. Staging bruto permanece proibido como fonte oficial de IA.

## 12. Estratégia de reversibilidade

A futura promoção deve ser aditiva e idempotente.

Requisitos:

- nenhum `UPDATE` destrutivo em CRM operacional;
- nenhuma exclusão automática;
- chave de idempotência por importação + hash do registro;
- lote de promoção identificável;
- possibilidade de despublicar/desconsiderar um lote analítico sem apagar a fonte ou staging;
- auditoria de quem autorizou e quando.

Rollback significa retirar o lote da camada oficial de consumo analítico, **não apagar a evidência histórica original**.

## 13. Gate final

**Resultado da HIST-007:** a arquitetura de promoção está formalmente definida, mas a promoção dos 906 registros continua bloqueada.

Motivo do bloqueio:

- `historico_staging` ainda não contém a carga física homologada;
- o manifesto quantitativo final de reconciliação ainda não foi materializado;
- portanto não existe base auditável para declarar quantos registros estão efetivamente elegíveis para promoção.

Próxima execução, somente mediante autorização expressa específica:

1. carregar a fonte homologada no `historico_staging`, com idempotência e proveniência;
2. executar normalização, reconciliação e auditoria sobre os 906 registros;
3. gerar o manifesto final com os quantitativos reais;
4. submeter esse manifesto à homologação humana;
5. somente depois criar/promover para a camada histórica/analítica oficial.

## 14. Proibições que permanecem vigentes

Mesmo após esta proposta:

- não criar oportunidades ativas a partir da planilha;
- não alterar Pipeline/Forecast atuais;
- não transformar BACKLOG em venda automaticamente;
- não sobrescrever clientes;
- não apagar registros ambíguos;
- não alimentar IA com staging bruto;
- não misturar implementadora com cliente final;
- não reescrever CARLA como MÔNICA no fato histórico;
- não promover nada sem novo gate explícito.

---

**Conclusão:** HIST-007 encerra o ciclo de desenho, preparação e homologação da estrutura histórica 2023–2026. O CTI está preparado para uma futura carga controlada e promoção analítica, mas **nenhum registro histórico foi promovido por esta execução**.
