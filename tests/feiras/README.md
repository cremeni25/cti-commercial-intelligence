# CTI Web / CRM App - Feiras CARRIER

Status: EM DESENVOLVIMENTO. NAO PUBLICAR como entrega homologada.

## Escopo desta continuidade

A branch existente foi continuada a partir de c27beb1500aab160cce1f0b8cee30b1478788176.
O site institucional nao foi editado. As interfaces alteradas sao /usuarios
(CTI Web) e /crm-app/feiras (CRM App), com seus mecanismos de sessao e acesso.
A producao, o banco principal e os aliases de publicacao nao foram alterados.

## Implementacao

- Cadastro institucional e selecao de empresa/papel no gerenciamento existente.
- Provisionamento atomico de perfil, permissoes e vinculo por RPC; compensacao
  da conta Auth se o cadastro falhar. Acesso externo limitado a Feiras.
- Barreira de autenticacao tambem nas rotas legadas: remover o token nao
  permite contornar as restricoes externas. Primeiro acesso exigido no backend.
- Filtro por criador e autorizada atual, incluindo relatorios. Transferir o
  profissional nao concede acesso aos registros da empresa anterior.
- Gravar atendimento e itens na mesma transacao. Repeticoes usam a mesma chave;
  conteudo diferente com a mesma chave e rejeitado e a pendencia e preservada.
- Cofre AES-GCM por usuario, PBKDF2, senha exclusiva, chave so em memoria,
  identificadores locais segregados, verificacao de integridade e bloqueio ao
  sair/ocultar. Fila antiga so e removida depois de copia cifrada confirmada.
- Paginacao de atendimentos e itens; PDF percorre todas as paginas autorizadas.

## Evidencias locais

- 74 testes Python de acesso, isolamento e regressao aprovados.
- 16 verificacoes no Chromium real de Web Crypto e IndexedDB aprovadas.
- 6 verificacoes do fluxo da tela CRM App, viewport 390x844, aprovadas.
- 15 verificacoes SQL em PostgreSQL WASM isolado aprovadas; exercicio de fila
  com 1, 10 e 50 requisicoes, sem erros. Isso NAO mede capacidade Render/Supabase
  nem concorrencia real de varias conexoes.
- TypeScript, lint dos arquivos alterados e build Next.js aprovados.
- A bateria Python integral nao foi homologada: execucoes limitadas por timeout.
  Os testes legados que acessavam rotas sem sessao foram adaptados para executar
  explicitamente como equipe interna; testes negativos de autenticacao continuam
  sem esse fixture e verificam 401/403.

Arquivos *-results.json descrevem o ambiente e os casos. A tela usa sessao
sintetica e transporte de API simulado; os testes HTTP usam o router real com
transporte Supabase simulado; SQL e Web Crypto executam seus mecanismos reais.
Nenhum desses resultados substitui a homologacao integrada remota autenticada.

## Reproducao

No frontend: npm ci; npm run build (variaveis Supabase de teste).
Nesta pasta: npm ci; npx playwright install chromium.
Executar npm run test:database, npm run test:vault e npm run test:ui.
CTI_CHROMIUM_EXECUTABLE permite usar um Chromium instalado no ambiente.
Os testes UI iniciam o Next localmente e bloqueiam chamadas externas.

Backend: instalar backend/requirements.txt, pytest e httpx[socks]; usar
SUPABASE_URL=https://example.supabase.co, SUPABASE_KEY=test-key e PYTHONPATH=backend.
O manifesto evidence-summary.json lista os modulos da bateria aprovada.

## Impedimentos e condicoes para publicacao

1. Provisionar ambiente remoto isolado. A tentativa de criar branch Supabase
   retornou Invalid or expired requestState; uma consulta posterior confirmou
   que nenhuma branch foi criada. Nao aplicar a migracao ao banco principal
   antes de validar esquema real, RLS, RPCs e permissoes nesse ambiente.
2. Homologar cadastro, edicao e revogacao institucional no CTI Web e sessao real
   do CRM App com duas empresas e varios profissionais. Nao foram criadas contas
   institucionais reais ou empresas ficticias na producao.
3. Concluir regressao completa do CTI. A barreira global tambem exige verificar
   chamadas legadas que antes omitiam token e fluxos documentais compartilhados.
4. Medir carga remota com conexoes reais, latencia, erros e recursos do servidor.
5. Validar partida a frio sem rede: o cofre recupera bytes apos recarga, mas a
   interface ainda depende de resolver perfil, feira e catalogo pela API. O
   funcionamento completo apos reiniciar o aplicativo sem conexao nao foi provado.
6. Validar recuperacao em aparelho compartilhado, troca/revogacao de conta,
   multiplas abas, falha durante migracao da fila antiga e limpeza dos caches.
   Pendencias antigas de outras contas permanecem no formato anterior ate
   migracao por seus titulares; nao declarar protecao retroativa sem conferir.
7. Validar transicao dos acessos internos existentes e politica de permissoes.
   O novo campo feiras_eventos nao foi aplicado nem atribuido na producao.
8. Definir/testar edicao de atendimento permitido conforme o documento canonico;
   o fluxo deste incremento cobre cadastro e sincronizacao de novos atendimentos.
9. Revisar migracao/rollback com backup, aprovar a homologacao e so entao publicar
   backend e frontend coordenadamente, com verificacao posterior dos dominios.

Este registro documenta progresso e limites. Nao e certificado de conclusao.
