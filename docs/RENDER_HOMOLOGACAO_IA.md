# Render separado — IA Comercial CTI em homologação

## Objetivo

Criar um novo serviço Render exclusivo para o agente experimental, sem modificar o serviço produtivo utilizado pela equipe comercial.

## Arquivo Blueprint

Usar o arquivo `render.homologacao.yaml` desta branch.

## Regras obrigatórias

- Nome do novo serviço: `cti-ia-agente-homologacao`.
- Branch: `fix-ia-web-quality`.
- Root directory: `backend`.
- Auto-deploy: desligado.
- Ambiente: `homologation`.
- Agente: habilitado somente nesse serviço.
- Modo: somente leitura.
- Não reutilizar o nome do serviço produtivo.
- Não apontar o domínio produtivo para este serviço.
- Não alterar as variáveis do Render produtivo.

## Segredos solicitados na criação

O Render solicitará os valores das variáveis marcadas com `sync: false`:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`

Esses valores não ficam gravados no repositório.

## Configurações fixas do serviço

```text
CTI_AMBIENTE=homologation
CTI_IA_AGENTE_HOMOLOGACAO=true
CTI_IA_AGENTE_SOMENTE_LEITURA=true
OPENAI_AGENT_MODEL=gpt-4.1-mini
OPENAI_AGENT_WEB_MODEL=gpt-4.1-mini
```

## Validação inicial

Após o primeiro deploy, validar nesta ordem:

1. `GET /ia-comercial-agente-homologacao/status`
2. autenticação com usuário `ADMIN_MASTER` de homologação;
3. confirmação de `somente_leitura: true`;
4. confirmação de `ambiente: homologation`;
5. `POST /ia-comercial-agente-homologacao/consultar` com pergunta interna;
6. nova consulta exigindo pesquisa web;
7. conferência das fontes retornadas;
8. execução da matriz de regressão documentada no PR #174.

## Bloqueio e rollback

Para desligar o agente no serviço de homologação:

```text
CTI_IA_AGENTE_HOMOLOGACAO=false
```

O serviço produtivo continua independente porque não usa esse Blueprint, essa branch nem essa feature flag.
