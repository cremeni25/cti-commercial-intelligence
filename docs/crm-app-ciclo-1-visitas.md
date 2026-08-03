# CRM App CTI — Ciclo 1: Visitas comerciais

## Responsabilidade do módulo

A tela `/crm-app/visitas` é responsável pela jornada operacional de visita em campo. Não é uma listagem genérica de atividades.

## Estados operacionais

- **Agendada:** visita futura ou prevista para hoje.
- **Atrasada:** data prevista vencida e visita ainda não concluída.
- **Em andamento:** profissional iniciou a execução.
- **Concluída:** resultado registrado e histórico sincronizado.

## Jornada

1. Agendar visita com cliente, oportunidade, data, horário e objetivo.
2. Preparar a visita consultando cliente ou histórico da oportunidade.
3. Iniciar visita.
4. Registrar resultado e desfecho.
5. Definir próxima ação e data.
6. Concluir e sincronizar o histórico comercial.

## Integração

- Fonte principal: `cti_atividades`, com `tipo = VISITA`.
- Cliente: Cadastro Mestre de Clientes.
- Oportunidade: núcleo comercial consolidado.
- Histórico: registrado automaticamente pelo backend quando existe `oportunidade_id`.
- Próxima ação: criada como atividade `FOLLOW_UP`, permanecendo na Agenda.

## Critério de validação

A tela não pode apresentar apenas um estado vazio. Mesmo sem visitas, deve oferecer a ação explícita **Agendar visita** e explicar o próximo passo operacional.
