# Handoff — estado em 2026-11-26

Branch de trabalho: `claude/fervent-cori-naf7zl` (repositório único: `cremeni25/cti-commercial-intelligence`,
backend e frontend no mesmo repo).

## Pronto e no ar
- **Etapa 1 – acervo e carteira** (#620): histórico preservado na troca de responsável, transferência de
  carteira, backup semanal (`acervo-backup.yml`, domingo 06:17 UTC), carteira setorizada (`/carteira`),
  ficha única da empresa, glossário.
- **Campanhas e Canal** (#621, `/campanhas`, gestão): 5 campanhas por grupo da carteira com mensagem por
  cliente, aprovação, envio por link do WhatsApp Business, exportação, autorização LGPD, posts semanais do Canal.
- **Pergunte ao CTI** (#622): botão + Ctrl/⌘K em todas as telas; busca (telas, empresas, modelos) e
  perguntas em linguagem comercial que abrem a Carteira já filtrada. Interpretação determinística (sem LLM).
- **Indicadores e comissões** (#623, #624, `/indicadores`, só Master): indicadores, indicações, venda
  concluída → comissão por equipamento, ciclo A pagar → NF recebida → Paga, painel (peso no vendido,
  por indicador/região/linha), extrato individual (CSV/impressão), sincronia com oportunidades ganhas/perdidas.
- Antes disso: carga de planilhas comerciais pelo CTI, app instalável, Feiras no app, link de senha (token_hash).

## Em andamento
- **PR #625 – tela "Hoje"** (Fase B): `/hoje`, primeiro item do menu; até 5 cartões (prioridades da Central,
  cliente da carteira a abordar, comissões a pagar para o Master); no app só o cartão de carteira.
  Testes locais ok (974 backend, build, navegador). Parou aguardando CI/revisão Codex → merge e verificação no ar.

## Próximos passos (prioridade)
1. Fechar o PR #625: ler achados do Codex, corrigir, merge squash, confirmar `/crm-seguro/hoje` no openapi.
2. Fase C: registrar/criar por conversa e voz no app (ex.: "registra visita na X…"), com confirmação.
3. Decidir se o login deve abrir em `/hoje` em vez de `/dashboard` (perguntar ao usuário).
4. WhatsApp Cloud API (modo coexistência) quando houver acesso Meta Business verificado; token via formulário.
5. Ampliar vocabulário do "Pergunte ao CTI" conforme termos que a equipe usar.

## Decisões e motivos
- Registros do agente no cofre (Storage) e não em tabelas novas: sem migração manual no banco.
- Interpretação do "Pergunte ao CTI" sem LLM: resposta imediata, sem custo; o resto vai para a IA Comercial
  (que hoje usa OpenAI; migrar para Claude exige chave da Anthropic do usuário).
- Valor da comissão gravado na venda: mudança de tabela não altera histórico.
- Indicadores só para o Master: decisão do usuário (indicador não tem acesso ao sistema).
- Tela inicial após login mantida no Dashboard até o usuário decidir.

## Problemas conhecidos / tentativas
- Gatilho `cti_sync_responsabilidade_cliente` reatribui atividades ao trocar responsável; mitigado no código
  (fotografia de autoria + diário em `acervo/autoria/`). Correção definitiva exige SQL no Supabase (oferecido).
- Commitar o pacote cifrado de planilhas foi bloqueado; solução adotada: upload pela tela do CTI.
- Teste `test_inteligencia_evolucao` dependia da data real; corrigido congelando a data no serviço.
- Ingestão semanal do SharePoint aguarda autorização do admin M365.

## Integrações (sem segredos)
- Render (backend), Vercel (frontend, 3 projetos de preview), Supabase (DB + bucket `cti-agente`),
  GitHub Actions com OIDC (`resumo-diario.yml`, `acervo-backup.yml`), revisão automática Codex nos PRs.
- Proxy Vercel limita respostas ~4,5 MB: downloads grandes por URL assinada do cofre.
