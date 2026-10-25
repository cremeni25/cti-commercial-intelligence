# Revisão operacional do CTI — 25/10/2026

## Proposta e lógica preservadas

O CTI sustenta a operação comercial da equipe: carteira de clientes, interações e retornos, oportunidades, propostas, pedidos e vendas. O portal oferece visão gerencial e inteligência comercial; o app conduz a execução em campo. O histórico de mercado alimenta análises e não deve ser confundido com oportunidades ou vendas da equipe. A IA interpreta informações e recomenda ações; não substitui a fonte operacional.

Fluxo a preservar: **cliente → interação → oportunidade → proposta → pedido → venda**, com responsável identificado, continuidade do histórico e autorização por perfil. Uma interação pode terminar sem gerar negócio. A emissão de documentos permanece vinculada ao processo existente.

Base examinada: `db5c72a7427f663c9e9480bfe65be9f087765754`, mesma revisão identificada no frontend de produção antes desta intervenção.

## Falhas confirmadas e correções

| Achado | Efeito anterior | Correção preparada |
|---|---|---|
| GET e POST `/crm-seguro/clientes` registrados em dois routers | A primeira implementação prevalecia; a listagem alternativa ignorava os filtros e o cadastro alternativo evitava as regras de responsabilidade/permissão do router canônico | Remoção dos dois handlers redundantes; manutenção do router canônico, com testes HTTP da aplicação real |
| Falha de uma fonte do resumo convertida em lista vazia | Indicador podia apresentar zero sem que a consulta tivesse sido concluída | Resposta inválida gera falha explícita; indicador indisponível apresenta `—` e aviso; fontes válidas permanecem disponíveis |
| Data de visitas baseada em UTC | Depois de 21h no Brasil, visitas do dia podiam deixar de entrar no indicador | Data civil local do dispositivo; timestamps convertidos para esse mesmo fuso |
| Atualização manual e periódica concorrentes | Consultas duplicadas e respostas antigas podiam sobrescrever a tela | Bloqueio de sobreposição, identificação da geração e vínculo do resumo ao usuário |
| “Continuar negociação” e “Proposta” abriam o mesmo destino | Duas escolhas aparentes para uma única jornada | Entrada única “Continuar negociação / proposta”, com explicação do próximo passo |
| Atalhos sem considerar todas as permissões | Usuário podia encontrar ações cujo destino seria negado | Aplicação do contrato de autorização existente à tela inicial, Nova ação e navegação inferior |
| Arquivamento de teste sem o transporte autenticado comum | A ação não fornecia explicitamente o token esperado pelo proxy | Uso do mesmo serviço autenticado das demais operações do CRM |
| Registro PWA atual removido a cada montagem | Abertura do app podia desfazer o registro existente, inclusive em situações de conectividade ruim | Somente o registro legado da raiz é removido; o registro atual é mantido e atualizado |
| Mensagem `SKIP_WAITING` enviada sem handler no service worker | Solicitação de ativação não era tratada | Handler explícito da mensagem |
| Carteira sem paginação e responsável consultado por cliente | Possibilidade de truncamento e centenas de consultas repetidas | Leitura ordenada em páginas até esgotar a fonte e responsáveis carregados em lotes; teste de 1.503 clientes com limite simulado de 137 registros por resposta |
| Testes com consultas Supabase não simuladas | Retentativas demoradas e possibilidade de alcançar um banco externo durante os testes | Bloqueio do transporte real Supabase no pytest; TestClient e transportes simulados permanecem disponíveis |

## Evidências locais

- Backend completo: **815 aprovados, 1 ignorado, 23 avisos**. Inclui regressões de paginação e leitura dos responsáveis em lote; frontend compilado e verificado em navegador.
- Regressões HTTP novas: uma única implementação para GET/POST de clientes; Master filtra responsável e não atribuídos; regional recebe só sua carteira; ausência de permissão impede listar/cadastrar.
- Build de produção Next.js e TypeScript: aprovado.
- Lint completo: zero erros e 52 avisos preexistentes. Arquivos frontend alterados: lint específico sem avisos.
- Testes semânticos de resumo/data: 2 aprovados.
- Chromium com build real, viewport de 390px e fontes sintéticas: 6 verificações aprovadas — falha parcial, atualização sem duplicação, dia brasileiro, ausência de rolagem horizontal, entrada única negociação/proposta e atalhos conforme permissões.
- Regressões existentes de Feiras: banco PostgreSQL isolado, esquema capturado, cofre, sessão, interface e modo offline executados com sucesso.
- CI ampliada para executar as regressões semânticas e a jornada inicial do CRM em navegador.

Nenhum teste acima representa autenticação com contas reais da equipe, validação de sua carteira em produção ou teste de capacidade do Supabase/Render.

## Produção observada

O domínio `app.cti-intelligence.com` pertence ao projeto Vercel `cti-commercial-intelligence-yri1`. O backend identificado no Render é `cti-backend`. A consulta de logs do backend desde 24/10/2026 não retornou entradas com nível de erro ou os textos procurados; ausência de entradas não comprova ausência de falhas.

A abertura do app publicado chegou à tela de login. Não havia sessão autenticada disponível neste navegador para conferir clientes, oportunidades e documentos reais. Não foram solicitadas senhas de integrantes da equipe nem alterados seus cadastros.

## Pontos de evolução ainda abertos

1. **Escala das carteiras:** a paginação e o enriquecimento em lote foram implementados nesta revisão. O tamanho de página e de lote limita somente cada consulta; não limita o total de clientes retornados. Medir latência com o volume operacional após a publicação.
2. **Reprodutibilidade do backend:** `requirements.txt` contém dependências sem versões fixas. Preparar um conjunto de versões homologadas antes de novos upgrades; a instalação futura pode resolver versões diferentes.
3. **Organização do código:** 6.018 arquivos rastreados estão em `backend/.venv`. Retirar dependências geradas do versionamento em uma alteração própria, verificando previamente que nenhum processo depende desse caminho. Não remover dados comerciais ou documentos de origem.
4. **Avisos frontend:** revisar os 52 avisos, especialmente dependências de efeitos em agenda, atividades e propostas. Não acrescentar dependências mecanicamente: isso pode introduzir recarregamentos repetidos.
5. **Validação operacional:** confirmar com sessão autorizada o percurso real cliente → interação → oportunidade → proposta → pedido, os totais por responsável, a continuidade no app instalado e os perfis efetivamente utilizados pela equipe. Não emitir nem enviar documentos reais apenas para testar.
6. **Entrega:** aprovação de testes é condição técnica, não homologação integral. Registrar a revisão publicada, acompanhar o deploy até terminar e conferir os fluxos reais antes de declarar encerrada a validação operacional.

Esta revisão reduz falhas identificadas e acrescenta proteção contra regressões. Não constitui promessa de ausência de bugs nem certificação integral do sistema em produção.
