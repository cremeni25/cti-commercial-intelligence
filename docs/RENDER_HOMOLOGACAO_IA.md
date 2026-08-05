# Render separado — IA Comercial CTI em homologação

## Objetivo

Criar um novo serviço Render exclusivo para o agente experimental, sem modificar o serviço produtivo utilizado pela equipe comercial.

## Isolamento obrigatório

- Serviço Render separado: `cti-ia-agente-homologacao`.
- Branch: `fix-ia-web-quality`.
- Root directory: `backend`.
- Auto-deploy: desligado.
- Projeto Supabase separado, criado exclusivamente para homologação.
- Nunca usar `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` ou qualquer segredo do projeto produtivo.
- O Blueprint solicita apenas `SUPABASE_URL`, `SUPABASE_KEY` e `OPENAI_API_KEY`.
- `SUPABASE_KEY` deve ser a chave pública/anon do projeto isolado de homologação.

## Preparação do Supabase isolado

1. Criar um novo projeto Supabase com nome identificável, por exemplo `cti-ia-homologacao`.
2. No SQL Editor desse projeto novo, executar somente:

```text
backend/migrations/homologacao/20260805_supabase_ia_homologacao_isolado.sql
```

3. Criar um usuário de teste no Auth do projeto novo.
4. Inserir o perfil correspondente em `cti_users`, usando o `auth_id` desse usuário.
5. Não copiar segredos, usuários ou dados sensíveis da produção.

O script cria tabelas mínimas, dados sintéticos e policies apenas de `SELECT`. Nenhuma policy de `INSERT`, `UPDATE` ou `DELETE` é criada.

## Segredos solicitados no Render

- `SUPABASE_URL`: URL do projeto Supabase isolado.
- `SUPABASE_KEY`: chave pública/anon do projeto Supabase isolado.
- `OPENAI_API_KEY`: chave do projeto OpenAI destinado à IA Comercial CTI.

## Configurações fixas

```text
CTI_AMBIENTE=homologation
CTI_IA_AGENTE_HOMOLOGACAO=true
CTI_IA_AGENTE_SOMENTE_LEITURA=true
OPENAI_AGENT_MODEL=gpt-4.1-mini
OPENAI_AGENT_WEB_MODEL=gpt-4.1-mini
```

## Validação inicial

1. `GET /ia-comercial-agente-homologacao/status`.
2. Autenticação com usuário de homologação.
3. Confirmação de `somente_leitura: true`.
4. Consulta interna sobre os dados sintéticos.
5. Consulta exigindo pesquisa web.
6. Conferência das fontes retornadas.
7. Tentativa controlada de escrita deve ser recusada pelo banco.

## Rollback

Definir:

```text
CTI_IA_AGENTE_HOMOLOGACAO=false
```

O serviço produtivo permanece independente deste Blueprint, desta branch e do Supabase isolado.
