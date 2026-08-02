# Arquitetura oficial do CTI

## Finalidade

Este documento estabelece a fonte oficial de verdade para os ambientes, domínios e responsabilidades técnicas do CTI Comercial Intelligence. Decisões futuras de ChatGPT, Codex, GitHub, Vercel e Render devem respeitar esta arquitetura e não reinterpretá-la sem decisão expressa do proprietário do projeto.

## Domínios oficiais

### Site institucional

- Endereço: `https://cti-intelligence.com`
- Finalidade: futuro site institucional do CTI.
- Não é backend.
- Não é a plataforma operacional.
- Não deve ser usado em variáveis de URL da API.

### Plataforma operacional

- Endereço: `https://app.cti-intelligence.com`
- Finalidade: plataforma de operações comerciais do CTI.
- Publicação: Vercel.
- Projeto oficial Vercel: `cti-commercial-intelligence-yri1`.
- Branch de produção: `main`.
- Root Directory: `frontend`.

### Aplicativo operacional

- Endereço: `https://app.cti-intelligence.com/crm-app`
- Finalidade: acesso, instalação como PWA e operação comercial em campo.
- O manifesto, o service worker, o cache e o escopo da PWA devem permanecer restritos a `/crm-app/`.
- O CRM App não é um sistema paralelo: utiliza o mesmo núcleo comercial da plataforma CTI.

### Backend

- Endereço: `https://cti-backend-5ugf.onrender.com`
- Serviço Render: `cti-backend`.
- Repositório: `cremeni25/cti-commercial-intelligence`.
- Branch de produção: `main`.
- Root Directory: `backend`.
- Runtime: Python 3 / FastAPI / Uvicorn.

## Repositório oficial

- GitHub: `cremeni25/cti-commercial-intelligence`.
- Branch oficial: `main`.
- O código de produção deve originar-se do `main` após validação por PR.
- Branches antigas, tentativas e recuperações não representam fonte de verdade enquanto não integradas ao `main`.

## Banco e autenticação

- Provedor: Supabase.
- Responsabilidades: PostgreSQL, autenticação, perfis, dados operacionais, CRM, ANFIR, produtos, propostas, aceites, pedidos, documentos e governança.
- O schema real do Supabase prevalece sobre modelos presumidos pelo código.
- Novas gravações não podem enviar colunas não comprovadas no schema vigente.

## Regras de integração

1. O frontend deve acessar o backend oficial por proxy interno controlado.
2. `cti-intelligence.com` e `app.cti-intelligence.com` nunca podem ser tratados como backend.
3. Variáveis de API devem apontar somente para `https://cti-backend-5ugf.onrender.com` ou para o proxy interno do frontend.
4. Respostas esperadas como JSON devem validar status e `content-type` antes do parse.
5. O CRM App deve preservar IDs e vínculos de oportunidade, proposta, aceite, pedido e dossiê.
6. Dashboard, Pipeline, Forecast, Funil Carrier, Pedidos e IA Comercial devem utilizar o núcleo comercial consolidado como fonte comum.
7. Fallbacks não podem mascarar silenciosamente perda de dados ou alteração de regra comercial.

## Ambientes Vercel

O projeto oficial conectado ao domínio `app.cti-intelligence.com` é:

- `cti-commercial-intelligence-yri1`

Os projetos abaixo foram identificados como duplicações de infraestrutura e não representam o ambiente oficial:

- `cti-commercial-intelligence`
- `cti-commercial-intelligence-8efr`

Eles não devem receber domínio oficial nem ser usados como referência de produção. Sua remoção ou desconexão deve ocorrer somente após comparação e preservação das variáveis necessárias do projeto oficial.

## Entradas DNS auxiliares

As entradas abaixo existem na UOL Host, mas não possuem função confirmada na arquitetura do CTI:

- `painel.cti-intelligence.com` → `painel.dominiotemporario.com`
- `sac.cti-intelligence.com` → `sac.uol.com.br`

Não devem ser alteradas ou removidas sem confirmação da UOL Host.

## Linha de base consolidada em 2 de agosto de 2026

- Frontend GitHub/Vercel: commit `73cf8ce9c542ad3598ab8e4d63ba5f2e4d0ef99d`.
- Backend Render: commit `22ef2df70db1ee6b173c1b534674468674001d45`.
- A diferença entre esses commits contém somente alterações em `frontend/`; portanto, a ausência de novo deploy do Render é coerente.
- PR #106 integrada: restauração do fluxo comercial real no CRM App.

## Autoridade de decisão

- Requisitos e regras comerciais: proprietário do CTI.
- Arquitetura e implementação: devem ser justificadas tecnicamente e registradas como decisões técnicas, nunca atribuídas ao usuário quando não foram determinadas por ele.
- ChatGPT e Codex não podem transformar decisões próprias em supostas instruções do usuário.
- Toda remoção, simplificação ou substituição de patrimônio funcional existente exige comprovação de necessidade e preservação do fluxo completo.
