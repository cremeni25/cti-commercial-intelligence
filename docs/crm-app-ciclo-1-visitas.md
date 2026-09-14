# CRM App CTI — Visitas comerciais

## Princípio

A visita é um fato comercial. O CRM App não transforma o vendedor em operador de workflow.

O módulo deve registrar somente o necessário para a execução em campo e, quando houver possibilidade real de negócio, encaminhar o acompanhamento para a oportunidade comercial até seu encerramento em ganho ou perda.

## Estados da visita

- **Agendada:** visita futura.
- **A confirmar:** a data da visita chegou ou passou e o sistema precisa apenas saber se ela ocorreu.
- **Realizada:** visita efetivamente ocorrida e preservada no histórico do cliente.
- **Não realizada:** visita que não aconteceu e foi encerrada como fato operacional.

Não existem mais estados obrigatórios de **Preparar visita**, **Iniciar visita** ou **Registrar resultado**.

## Jornada mínima

1. Agendar visita com cliente, data, objetivo e, quando já existir, oportunidade relacionada.
2. Na data da visita, confirmar apenas **Visita realizada** ou **Não realizada**.
3. Se a visita realizada já pertence a uma oportunidade, continuar diretamente no negócio.
4. Se ainda não existe oportunidade, responder apenas se surgiu possibilidade comercial.
5. Sem possibilidade comercial, a visita termina e permanece no dossiê.
6. Com possibilidade comercial, abrir oportunidade e acompanhar o mesmo ciclo até **ganho** ou **perda**.

## Regra comercial

O ciclo não precisa obedecer a uma sequência artificial de telas. Ele pode evoluir conforme a realidade do negócio, por exemplo:

- visita → oportunidade → proposta → pedido → venda;
- visita → oportunidade → venda;
- outra interação comercial → oportunidade → proposta → venda.

Proposta e pedido são marcos do mesmo ciclo comercial, não novos processos independentes.

As datas de abertura, fechamento previsto e fechamento real pertencem ao acompanhamento da oportunidade e servem para medir duração, atraso, conversão e resultado comercial.

## Integração

- Visitas continuam na fonte operacional `cti_atividades`.
- Cliente continua no Cadastro Mestre de Clientes.
- Oportunidade continua no núcleo comercial consolidado.
- O dossiê do cliente preserva as visitas e demais interações como histórico.
- Quando existe `oportunidade_id`, a continuidade é feita no próprio negócio.

## Critério de validação

A tela de visitas deve permitir agendar, confirmar ocorrência e abrir/continuar o ciclo comercial. Depois que uma visita é finalizada, não deve oferecer comandos administrativos sem sentido comercial.