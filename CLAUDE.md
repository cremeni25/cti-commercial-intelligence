# CTI — Centro de Tecnologia e Inteligência Comercial

BI + CRM + leitura comercial da Viena Refrigeração (representante Carrier Transicold, SP),
focado no transporte refrigerado (frigorífico). Responder ao usuário sempre em **português**.

## Como funciona
- Backend FastAPI (Render: `cti-backend-5ugf.onrender.com`) → Supabase (Postgres + Storage).
- Frontend Next.js 16 / React 19 / Tailwind 4 (Vercel: `app.cti-intelligence.com`); app PWA em `/crm-app`.
- O frontend fala com o backend pelo proxy `/api/crm-proxy/...` (`fetchCrmSeguroProxy`).
- Dados privados do agente (campanhas, indicações, acervo, planilhas) ficam no bucket privado
  `cti-agente` via `backend/services/cofre_agente.py` (um JSON por registro; listagem paginada).
- Rotinas agendadas: GitHub Actions autenticadas por OIDC (`core/github_oidc.py`).

## Estrutura
- `backend/routers/*_router.py` (registrar em `backend/main.py`), `backend/services/`, `backend/tests/`
  (fakes: `tests/supabase_memoria.py`, `tests/cofre_falso.py`).
- `frontend/src/app/<rota>/page.tsx`, `frontend/src/services/*.ts`, `frontend/src/components/`.
- Permissões de tela: `frontend/src/core/rbac/route-access.ts` (`rotaAutorizadaCTI`) **e** o gate
  próprio do menu em `frontend/src/components/ui/Sidebar.tsx` (atualizar os dois).
- Gestão = `ADMIN_MASTER`, ou `DIRETOR_VIENA_SP` com `acesso_total`.

## Comandos
- Testes backend: `cd backend && SUPABASE_URL=https://example.supabase.co SUPABASE_KEY=test-key pytest -q -p no:cacheprovider`
- Frontend: `cd frontend && npx eslint <arquivos> && npx tsc --noEmit -p .`
- Build: `NEXT_PUBLIC_SUPABASE_URL=https://example.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=isolated-test-key npm run build`
  e `npx next start -p <porta>`; testes de tela com Playwright e APIs simuladas.

## Regras do usuário
- Tudo automatizado ("não faço nada manual"); o módulo executa, não é chat.
- Merge automático (squash) quando o CI estiver verde e os achados da revisão Codex resolvidos.
- Repositório **público**: nunca commitar dados de clientes, planilhas (`*.xlsx/.xlsm/.xls` no
  `.gitignore`) ou PDFs originais. Dados entram pela tela de carga do CTI.
- Segredos só pelo formulário seguro (`request_credential`); nunca pedir chave no chat.
- Nada de identificador de modelo em commits/PRs. E-mail do usuário é privado.
- Desenvolver no branch `claude/fervent-cori-naf7zl`; sem force push (usar merge, não rebase).
- Não remover telas nem caminhos: evoluir para tornar o sistema interativo.
- Indicadores e comissões: uso **exclusivo do Master** (indicador não acessa o CTI nem o app).
- Comissão por equipamento: Trailer R$ 1.400 · Diesel Truck R$ 900 · Direct Drive R$ 400.
- WhatsApp: Canal "CTI Viena SP" + conversas 1:1 pela API oficial; sem grupos de clientes (LGPD).

**Ao final de cada etapa, atualize docs/HANDOFF.md e faça commit e push.**
