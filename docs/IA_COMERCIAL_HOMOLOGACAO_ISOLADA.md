# IA Comercial CTI — Homologação isolada

## Objetivo

Construir o novo agente da IA Comercial sem substituir, interromper ou modificar os fluxos operacionais atualmente usados pela equipe comercial.

## Regra principal

A nova arquitetura permanece fora da produção até que todos os testes técnicos e operacionais sejam aprovados.

## Isolamento obrigatório

- Branch exclusiva: `fix-ia-web-quality`.
- Nenhum merge automático para `main`.
- Rota experimental independente: `/ia-comercial-agente-homologacao`.
- A rota somente é registrada quando `CTI_IA_AGENTE_HOMOLOGACAO=true`.
- A configuração padrão é desligada.
- O agente bloqueia execução quando `CTI_AMBIENTE=production`.
- O agente bloqueia execução quando `CTI_IA_AGENTE_SOMENTE_LEITURA=false`.
- Nenhuma ferramenta de escrita será registrada durante a homologação.
- Nenhuma migration operacional será aplicada para esta fase.

## Variáveis do ambiente de homologação

```text
CTI_AMBIENTE=homologation
CTI_IA_AGENTE_HOMOLOGACAO=true
CTI_IA_AGENTE_SOMENTE_LEITURA=true
OPENAI_AGENT_MODEL=gpt-4.1-mini
OPENAI_AGENT_WEB_MODEL=gpt-4.1-mini
```

Essas variáveis não devem ser aplicadas ao serviço de produção utilizado pela equipe.

## Fluxos que não podem ser alterados

1. Login, sessão e perfis.
2. APP CRM.
3. Cadastro e consulta de oportunidades.
4. Pipeline e forecast.
5. Atividades e visitas.
6. Propostas e documentos oficiais.
7. Aceites, pedidos e dossiers.
8. Dashboard Executivo.
9. Upload operacional e ANFIR.
10. Cadastros de clientes, implementadoras, locadoras e usuários.

## Matriz mínima de regressão

Antes de qualquer proposta de ativação, validar no ambiente atual e repetir na homologação:

| Fluxo | Resultado obrigatório |
|---|---|
| Login ADMIN_MASTER | autentica e mantém perfil correto |
| Login comercial | autentica e respeita território |
| Criar oportunidade | salva e aparece no CTI |
| Abrir pipeline | mantém etapas e valores |
| Gerar proposta | usa o modelo Carrier correto |
| Visualizar Word | preserva documento oficial |
| Registrar aceite | cria vínculo correto |
| Abrir pedido | carrega modelo, cliente e valor |
| Dashboard | mantém indicadores existentes |
| APP CRM | continua sincronizando com o CTI |
| IA atual | continua disponível sem depender do agente novo |

## Critério de aprovação

O agente somente poderá ser considerado para ativação quando:

- operar em serviço Render separado;
- usar Preview Vercel separado;
- não registrar diferenças nos fluxos da matriz de regressão;
- demonstrar pesquisa web real com fontes verificáveis;
- consultar dados internos sem escrita;
- respeitar o perfil do usuário em cada ferramenta;
- registrar auditoria completa;
- receber autorização expressa do proprietário do CTI.

## Rollback

Como a rota experimental depende de feature flag, o desligamento é feito removendo ou definindo:

```text
CTI_IA_AGENTE_HOMOLOGACAO=false
```

O CTI operacional e a IA atual permanecem independentes dessa flag.
