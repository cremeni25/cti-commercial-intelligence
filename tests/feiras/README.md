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
- Edicao usa o mesmo formulario e cofre, com versao esperada e recibo idempotente.
  Profissional/gestor externo edita apenas os proprios registros da empresa
  atual; gestao interna com escopo global pode editar conforme seu acesso.
  Atendimento convertido nao aceita nova edicao; recibos perdidos continuam
  recuperaveis apos conversao ou mudanca no catalogo, sem reaplicar a operacao.
- Cofre AES-GCM por usuario, PBKDF2, senha exclusiva, chave so em memoria,
  identificadores locais segregados, verificacao de integridade e bloqueio ao
  sair/ocultar. Fila antiga so e removida depois de copia cifrada confirmada.
- Paginacao de atendimentos e itens; PDF percorre todas as paginas autorizadas.

## Evidencias locais

- 90 testes Python de acesso, isolamento e regressao aprovados.
- 24 verificacoes no Chromium real de Web Crypto e IndexedDB aprovadas,
  incluindo contexto offline cifrado, expiracao e desbloqueio interrompido.
- 9 verificacoes de sessao aprovadas no Chromium: saida offline, tokens do projeto
  correto, recarga e respostas atrasadas apos saida.
- 9 verificacoes do fluxo da tela CRM App, viewport 390x844, aprovadas.
- 14 verificacoes da partida a frio offline, reconexao e saida em varias abas
  aprovadas com service worker, CacheStorage, IndexedDB e Web Crypto reais,
  incluindo encerramento e reinicio do processo do navegador, sem espelho em
  sessionStorage, e abertura pela URL inicial do app instalado.
  Conta sintetica e servidor de API local: nao e homologacao do backend remoto.
- 34 verificacoes SQL em PostgreSQL WASM isolado aprovadas; exercicio de fila
  com 1, 10 e 50 requisicoes, sem erros. Isso NAO mede capacidade Render/Supabase
  nem concorrencia real de varias conexoes.
- TypeScript, lint dos arquivos alterados e build Next.js aprovados.
- A bateria integral do codigo 464c1fbc passou no GitHub: 809 aprovados,
  1 ignorado e 23 avisos; lint/build e testes SQL/cofre/sessao/UI/offline tambem
  passaram na execucao 39620858272. Essa rodada inclui 13 verificacoes offline;
  o teste adicional de reinicio de processo passou localmente apos essa rodada.
  Isso nao substitui verificacao funcional remota.
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
Executar npm run test:database, npm run test:vault, npm run test:session,
npm run test:ui e npm run test:offline. As variaveis NEXT_PUBLIC_SUPABASE_URL
e NEXT_PUBLIC_SUPABASE_ANON_KEY devem estar presentes no build. Usar
NEXT_PUBLIC_SUPABASE_URL=https://example.supabase.co e
NEXT_PUBLIC_SUPABASE_ANON_KEY=isolated-test-key para estes testes sinteticos.
CTI_CHROMIUM_EXECUTABLE permite usar um Chromium instalado no ambiente.
Os testes UI iniciam o Next localmente e bloqueiam chamadas externas.

Backend: instalar backend/requirements.txt, pytest e httpx[socks]; usar
SUPABASE_URL=https://example.supabase.co, SUPABASE_KEY=test-key e PYTHONPATH=backend.
O manifesto evidence-summary.json lista os modulos da bateria aprovada.

## Impedimentos e condicoes para publicacao

1. Provisionar ambiente remoto isolado. A tentativa de criar branch Supabase
   voltou a retornar Invalid or expired requestState nesta continuidade; consulta confirmou
   que nenhuma branch foi criada. Nao aplicar a migracao ao banco principal
   antes de validar esquema real, RLS, RPCs e permissoes nesse ambiente.
2. Homologar cadastro, edicao e revogacao institucional no CTI Web e sessao real
   do CRM App com duas empresas e varios profissionais. Nao foram criadas contas
   institucionais reais ou empresas ficticias na producao.
3. Concluir regressao completa do CTI. A barreira global tambem exige verificar
   chamadas legadas que antes omitiam token e fluxos documentais compartilhados.
4. Medir carga remota com conexoes reais, latencia, erros e recursos do servidor.
5. Repetir no ambiente remoto o fluxo local de partida a frio sem rede. O
   contexto de perfil/feiras/catalogo agora fica cifrado e vinculado a identidade
   Auth, sem tokens no cofre. O acesso offline termina quando a sessao ou o
   contexto expira; pendencias sao preservadas. O worker guarda somente shell e
   arquivos estaticos e nao respostas de APIs. Saida local nao depende da rede
   e bloqueia restauracao tardia. Isso encerra a sessao deste aparelho, sem
   revogar sessoes em outros aparelhos no servidor.
6. Validar recuperacao em aparelho compartilhado, troca/revogacao de conta,
   multiplas abas, falha durante migracao da fila antiga e limpeza dos caches.
   Pendencias antigas de outras contas permanecem no formato anterior ate
   migracao por seus titulares; nao declarar protecao retroativa sem conferir.
7. Validar transicao dos acessos internos existentes e politica de permissoes.
   O novo campo feiras_eventos nao foi aplicado nem atribuido na producao.
8. Homologar remotamente a edicao implementada: conflitos mantem pendencias
   cifradas e exigem conferencia, sem sobrescrever automaticamente outra versao.
   O incremento cobre cadastro, edicao permitida e sincronizacao idempotente.
9. Revisar migracao/rollback com backup, aprovar a homologacao e so entao publicar
   backend e frontend coordenadamente, com verificacao posterior dos dominios.

Este registro documenta progresso e limites. Nao e certificado de conclusao.


## Homologação Supabase real — 21/10/2026

O projeto existente `cti-ia-homologacao` (`xhrikmksydsyalxkkyot`) estava vazio.
A estrutura de seis tabelas foi reproduzida da produção, sem copiar registros,
contas ou credenciais. As funções de cadastro, criação e edição foram instaladas.
`remote/supabase-results.json` registra **11 verificações aprovadas no PostgreSQL
remoto**, com dados sintéticos revertidos ao terminar. Consulta posterior
confirmou zero perfis, atendimentos e contas Auth de teste remanescentes.

O primeiro teste revelou que `jsonb_populate_record(null, ...)` não aplica os
valores padrão da tabela: o cadastro externo falhava no `updated_at` obrigatório.
A correção também preenche as permissões booleanas obrigatórias. Essa parte foi
aplicada e passou na homologação. A revisão seguinte acrescentou rejeição de
perfil sem tipo e papel institucional nulo. A aplicação remota desse complemento
retornou **Migration was declined**; não foi repetida. Assim, os **13 casos locais**
em `production-schema-results.json` não equivalem a 13 casos remotos aprovados.

Reprodução local com o esquema capturado: `npm run test:production-schema`.
A CI executa esse teste e reaplica as migrações para conferir repetibilidade.
O arquivo `remote/real-database-regression.sql` contém o conjunto atualizado de
13 casos e só deve ser executado no projeto de homologação, após o complemento.
O baseline exige esquema público vazio; não deve ser reaplicado nesse projeto.

Ainda faltam autenticação real, backend e frontend isolados integrados, teste
funcional dos dois aplicativos e carga com conexões reais. A produção permanece
sem estas migrações. Nenhum resultado SQL isolado comprova o fluxo completo.
