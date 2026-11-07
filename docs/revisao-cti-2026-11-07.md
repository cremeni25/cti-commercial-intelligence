# Revisão CTI — 07/11/2026

Base: `ded5a74`. Objetivo: simplificar a devolutiva dos dados, organizar a inteligência por meio de um agente e preparar a plataforma para novos módulos, sem alterar o fluxo comercial em operação (cliente → interação → oportunidade → proposta → pedido → venda).

## Falhas confirmadas e corrigidas

| Achado | Efeito | Correção |
|---|---|---|
| `nucleo_comercial` devolvia probabilidade `1.0` (escala 0–1) para PEDIDO/DOSSIÊ/CARRIER/FATURADO, mas calculava `valor_ponderado = valor × prob / 100` | O valor ponderado dos negócios em pedido saía com 1% do valor real; Forecast e Funil Carrier somavam esse valor | Escala única de 0 a 100 (`100.0`), com teste de regressão |
| A página Forecast exibia a probabilidade como `p × 100` | Um negócio de 50% aparecia como "5000%" | Normalização igual à das demais telas (`p ≤ 1 ? p×100 : p`) |

## Novidades (aditivas)

- **Agente de Inteligência Comercial** (`backend/services/inteligencia_comercial/`): briefing priorizado, explicado e auditável; sinais organizados por provedor e por módulo. Ver `docs/AGENTE_INTELIGENCIA_COMERCIAL.md`.
- **Central de Inteligência** (`/central`): primeiro item do menu do portal, com uma tela única de prioridades, riscos, funil, confiabilidade dos dados e módulos.
- **Prioridades no app:** card na tela inicial, abaixo das ações principais, e a tela `/crm-app/prioridades`.
- **IA Comercial:** passa a ler a fonte `prioridades_comerciais`, com o mesmo raciocínio da Central e sem nova ferramenta nem mudança nas guardas existentes.
- **Registro de módulos** (`backend/core/modulos_plataforma.py`): fonte única do que a plataforma faz, com Catálogo (em evolução) e Treinamentos (em breve) já declarados.
- **Repositório:** `backend/.venv` (6.018 arquivos, ligado a um Python de Codespace inexistente) foi retirado do versionamento, em commit próprio. O Render instala a partir de `requirements.txt`.

## Evidências locais

- Backend: **870 aprovados**, 1 ignorado (linha de base: 832), incluindo 38 testes novos (regras, escopo HTTP, isolamento de falhas, IA e rotas de módulos).
- Frontend: TypeScript e build de produção aprovados; lint dos arquivos alterados sem avisos.
- Chromium real com build Next e APIs sintéticas: `central-browser.mjs` (6 verificações, incluindo backend antigo/404 sem quebrar a tela inicial e data civil brasileira) e `crm-home-browser.mjs` (7 verificações já existentes, todas mantidas).

Nenhum teste usou contas reais ou dados de produção. Após o deploy, conferir com sessão autorizada: a leitura de um vendedor (somente a própria carteira), a visão consolidada do Master e a calibração dos limiares com a gestão comercial.

## Ordem de publicação

O frontend tolera um backend anterior: sem o endpoint, o card do app não aparece e a Central mostra um aviso. O ideal é publicar o backend (Render) antes ou junto do frontend (Vercel).

## Segunda entrega do mesmo dia: ação e catálogo

- **Resolver direto da prioridade:** agendar o próximo passo, concluir, reagendar e "não se aplica/adiar" com motivo. A lista é limpa na hora e a leitura é refeita.
- **Calibração do agente:** ajustes ficam registrados com autor e motivo; leitura de aprendizado para a gestão.
- **Catálogo de produtos** no portal e no app, com os 17 materiais do Linktree oficial mapeados por modelo e por linha e o resumo pronto para WhatsApp.
- **App:** indicadores em formato compacto (ex.: "R$ 2,35 mi") para não cortar valores em 390px.
- **Evidências:** backend com 885 aprovados; navegador com 10 verificações novas e as 7 existentes mantidas.
- ~~Pendente no banco~~: substituído pelo cofre do agente, criado automaticamente (ver a quarta entrega).

## Terceira entrega: resumo diário no celular

- **Web Push com chaves VAPID:** inscrição por aparelho na tela de Prioridades e envio nos dias úteis às 07:40, a partir da leitura do agente no escopo de cada pessoa.
- **Privacidade e respeito:** sem valores na tela bloqueada, sem envio quando não há prioridades, perfil relido no envio e aparelhos expirados desativados.
- **Disparo:** endpoint interno `/interno/notificacoes/resumo-diario`, protegido por `CTI_CRON_TOKEN` com comparação em tempo constante. É a única exceção pública acrescentada à fronteira de autenticação, e há teste que confirma que as demais rotas continuam exigindo sessão.
- **Correção encontrada pelo teste:** sem service worker registrado, a ativação esperava para sempre; agora o limite é de 5 s, com mensagem.
- **Evidências:** backend com 892 aprovados; navegador com 12 verificações (duas execuções seguidas) e as 7 existentes mantidas; criptografia aes128gcm e assinatura VAPID validadas localmente com chaves reais geradas no teste.
- ~~Pendente: migração, variáveis e secrets~~: eliminados na quarta entrega.

## Quarta entrega: zero passo manual

A pedido do proprietário ("não faço nada manual"):

- **Sem migrações:** ajustes de alertas e inscrições passam ao cofre do agente, um bucket privado `cti-agente` criado pelo próprio backend com a chave de serviço existente. As duas migrações desta branch foram removidas antes de chegar à `main`.
- **Sem chaves para gerar:** o par VAPID é gerado na primeira utilização e guardado no cofre, com criação exclusiva entre instâncias.
- **Sem secrets no GitHub:** o agendamento se autentica por OIDC do GitHub, com validação de emissor, público, repositório, branch `main`, workflow e evento, além de testes de rejeição para cada desvio.
- **Envio idempotente por dia:** marca exclusiva no cofre.
- **Privacidade:** um aparelho usado por outra pessoa passa a ser dela; a inscrição anterior é removida.
- **CI:** o job `frontend-validation` foi fixado em `ubuntu-24.04`, porque o `ubuntu-latest` passou a 26.04, sem suporte do Playwright 1.56.1.
- **Evidências:** backend com 905 aprovados; envio real do `pywebpush` com chave autogerada validado contra POST interceptado (aes128gcm, VAPID e TTL).
